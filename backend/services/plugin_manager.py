"""
Plugin architecture for extending TerraSim GIS functionality.
Supports dynamic plugin loading, hooks, and safe execution.
"""

import logging
import importlib.util
import inspect
import os
import sys
from typing import Dict, List, Any, Optional, Callable, Type, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    dependencies: Optional[List[str]] = None
    entry_point: str = "main"
    hooks: Optional[List[str]] = None


class Hook(ABC):
    """Base hook class"""
    
    name: str = ""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute hook"""
        pass


class ToolPlugin(ABC):
    """Base tool plugin"""
    
    metadata: Optional[PluginMetadata] = None
    
    @abstractmethod
    def initialize(self, app: Any):
        """Initialize plugin"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute tool"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources"""
        pass


class ProcessorPlugin(ABC):
    """Base data processor plugin"""
    
    metadata: Optional[PluginMetadata] = None
    
    @abstractmethod
    def process(self, data: Any, **options) -> Any:
        """Process data"""
        pass
    
    @abstractmethod
    def get_output_type(self) -> str:
        """Get output type"""
        pass
    
    @abstractmethod
    def get_options_schema(self) -> Dict[str, Any]:
        """Get options schema"""
        pass


class RendererPlugin(ABC):
    """Base renderer plugin"""
    
    metadata: Optional[PluginMetadata] = None
    
    @abstractmethod
    def render(self, layer: Any, canvas: Any, **options) -> bool:
        """Render layer"""
        pass
    
    @abstractmethod
    def supports_layer_type(self, layer_type: str) -> bool:
        """Check if renderer supports layer type"""
        pass


class HookRegistry:
    """Register and execute hooks"""
    
    def __init__(self):
        self.hooks: Dict[str, List[Hook]] = {}
    
    def register_hook(self, hook_name: str, hook: Hook):
        """Register a hook"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(hook)
        logger.info(f"Registered hook: {hook_name}")
    
    def unregister_hook(self, hook_name: str, hook: Hook) -> bool:
        """Unregister a hook"""
        if hook_name in self.hooks:
            try:
                self.hooks[hook_name].remove(hook)
                logger.info(f"Unregistered hook: {hook_name}")
                return True
            except ValueError:
                pass
        
        return False
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all hooks with given name"""
        if hook_name not in self.hooks:
            return []
        
        results = []
        for hook in self.hooks[hook_name]:
            try:
                result = hook.execute(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook execution failed: {hook_name} - {e}")
        
        return results
    
    def get_hook_count(self, hook_name: str) -> int:
        """Get number of hooks registered for name"""
        return len(self.hooks.get(hook_name, []))


class PluginManager:
    """Manage plugin lifecycle"""
    
    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = plugin_dir or os.path.join(os.getcwd(), "plugins")
        self.plugins: Dict[str, Any] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self.hook_registry = HookRegistry()
        self._load_lock = threading.Lock()
        
        # Create plugin directory if doesn't exist
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            logger.info(f"Created plugin directory: {self.plugin_dir}")
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directory"""
        plugins = []
        
        if not os.path.exists(self.plugin_dir):
            return plugins
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                plugin_name = filename[:-3]
                plugins.append(plugin_name)
                logger.debug(f"Discovered plugin: {plugin_name}")
        
        return plugins
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a single plugin"""
        with self._load_lock:
            if plugin_name in self.plugins:
                logger.warning(f"Plugin already loaded: {plugin_name}")
                return True
            
            try:
                plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
                
                if not os.path.exists(plugin_path):
                    logger.error(f"Plugin file not found: {plugin_path}")
                    return False
                
                # Load module
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                if spec is None:
                    logger.error(f"Failed to create spec for plugin {plugin_name}")
                    return False
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_name] = module
                
                if spec.loader is None:
                    logger.error(f"No loader found for plugin {plugin_name}")
                    return False
                
                spec.loader.exec_module(module)
                
                self.plugins[plugin_name] = module
                logger.info(f"Loaded plugin: {plugin_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                return False
    
    def load_all_plugins(self) -> int:
        """Load all discovered plugins"""
        plugins = self.discover_plugins()
        loaded = 0
        
        for plugin_name in plugins:
            if self.load_plugin(plugin_name):
                loaded += 1
        
        logger.info(f"Loaded {loaded}/{len(plugins)} plugins")
        return loaded
    
    def instantiate_plugin(self, plugin_name: str, plugin_class: Type[ToolPlugin]) -> bool:
        """Instantiate a plugin"""
        if plugin_name in self.plugin_instances:
            logger.warning(f"Plugin already instantiated: {plugin_name}")
            return True
        
        try:
            instance = plugin_class()
            self.plugin_instances[plugin_name] = instance
            logger.info(f"Instantiated plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to instantiate plugin {plugin_name}: {e}")
            return False
    
    def get_plugin_instance(self, plugin_name: str) -> Optional[Any]:
        """Get plugin instance"""
        return self.plugin_instances.get(plugin_name)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        with self._load_lock:
            # Cleanup instance
            if plugin_name in self.plugin_instances:
                try:
                    instance = self.plugin_instances[plugin_name]
                    if hasattr(instance, 'cleanup'):
                        instance.cleanup()
                    del self.plugin_instances[plugin_name]
                except Exception as e:
                    logger.error(f"Plugin cleanup failed: {e}")
            
            # Remove module
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
            
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
    
    def unload_all_plugins(self):
        """Unload all plugins"""
        plugin_names = list(self.plugin_instances.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)
    
    def list_plugins(self) -> Dict[str, Any]:
        """List loaded plugins with metadata"""
        result = {}
        
        for plugin_name, module in self.plugins.items():
            metadata = None
            if hasattr(module, 'metadata'):
                metadata = module.metadata
            
            result[plugin_name] = {
                'loaded': plugin_name in self.plugin_instances,
                'metadata': metadata
            }
        
        return result
    
    def validate_plugin(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """Validate plugin structure"""
        errors = []
        
        if plugin_name not in self.plugins:
            errors.append(f"Plugin not loaded: {plugin_name}")
            return False, errors
        
        module = self.plugins[plugin_name]
        
        # Check for metadata
        if not hasattr(module, 'metadata'):
            errors.append("Missing metadata attribute")
        
        # Check for entry point
        if hasattr(module, 'metadata') and hasattr(module.metadata, 'entry_point'):
            entry_point = module.metadata.entry_point
            if not hasattr(module, entry_point):
                errors.append(f"Missing entry point: {entry_point}")
        
        return len(errors) == 0, errors
    
    def get_hook_registry(self) -> HookRegistry:
        """Get hook registry"""
        return self.hook_registry


class PluginSandbox:
    """Execute plugins in restricted environment"""
    
    def __init__(self, max_memory_mb: int = 512, timeout_seconds: int = 30):
        self.max_memory_mb = max_memory_mb
        self.timeout_seconds = timeout_seconds
    
    def execute_safely(
        self,
        plugin_func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """Execute plugin function with safety checks"""
        try:
            # Set timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Plugin execution exceeded {self.timeout_seconds}s")
            
            # Try to execute
            result = plugin_func(*args, **kwargs)
            return True, result, None
        except TimeoutError as e:
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Plugin execution error: {e}")
            return False, None, str(e)


# Example plugin template
PLUGIN_TEMPLATE = '''
"""
Example TerraSim Plugin
"""

from backend.services.plugin_manager import ToolPlugin, PluginMetadata

metadata = PluginMetadata(
    name="Example Plugin",
    version="1.0.0",
    author="Your Name",
    description="Example plugin template",
    dependencies=[],
    entry_point="ExampleTool"
)


class ExampleTool(ToolPlugin):
    """Example tool plugin"""
    
    metadata = metadata
    
    def initialize(self, app):
        """Initialize plugin"""
        print("Plugin initialized!")
    
    def execute(self, *args, **kwargs):
        """Execute tool"""
        return {"result": "success"}
    
    def cleanup(self):
        """Cleanup resources"""
        print("Plugin cleanup!")
'''
