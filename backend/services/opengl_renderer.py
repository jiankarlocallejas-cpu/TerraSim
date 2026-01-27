"""
OpenGL Rendering Engine for TerraSim
Provides GPU-accelerated 3D terrain visualization and real-time erosion rendering
"""

import numpy as np
import logging
import ctypes
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from OpenGL.GL import *  # type: ignore
    from OpenGL.GLU import *  # type: ignore
    from OpenGL.GL.shaders import compileProgram, compileShader  # type: ignore
    import pygame  # type: ignore
    from pygame.locals import *  # type: ignore
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    logger.warning("OpenGL libraries not available. Install PyOpenGL and pygame.")
    # Define stub constants to prevent unbound errors in type checker
    DOUBLEBUF = 0  # type: ignore
    OPENGL = 0  # type: ignore
    GL_DEPTH_TEST = 0  # type: ignore
    GL_LIGHTING = 0  # type: ignore
    GL_LIGHT0 = 0  # type: ignore
    GL_VERTEX_SHADER = 0  # type: ignore
    GL_FRAGMENT_SHADER = 0  # type: ignore
    GL_FRONT_AND_BACK = 0  # type: ignore
    GL_AMBIENT = 0  # type: ignore
    GL_DIFFUSE = 0  # type: ignore
    GL_SPECULAR = 0  # type: ignore
    GL_POSITION = 0  # type: ignore
    GL_SHININESS = 0  # type: ignore
    GL_ARRAY_BUFFER = 0  # type: ignore
    GL_ELEMENT_ARRAY_BUFFER = 0  # type: ignore
    GL_STATIC_DRAW = 0  # type: ignore
    GL_FLOAT = 0  # type: ignore
    GL_TRIANGLES = 0  # type: ignore
    GL_UNSIGNED_INT = 0  # type: ignore
    GL_COLOR_BUFFER_BIT = 0  # type: ignore
    GL_DEPTH_BUFFER_BIT = 0  # type: ignore
    GL_PROJECTION = 0  # type: ignore
    GL_MODELVIEW = 0  # type: ignore
    def glEnable(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glClearColor(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glLight(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glMaterial(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glGenVertexArrays(*args: any, **kwargs: any) -> int: return 0  # type: ignore
    def compileShader(*args: any, **kwargs: any) -> int: return 0  # type: ignore
    def compileProgram(*args: any, **kwargs: any) -> int: return 0  # type: ignore
    def glBindVertexArray(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glGenBuffers(*args: any, **kwargs: any) -> int: return 0  # type: ignore
    def glBindBuffer(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glBufferData(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glGetAttribLocation(*args: any, **kwargs: any) -> int: return 0  # type: ignore
    def glVertexAttribPointer(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glEnableVertexAttribArray(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glUseProgram(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glDrawElements(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glBegin(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glColor3fv(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glVertex3fv(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glEnd(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glClear(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glMatrixMode(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def glLoadIdentity(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def gluPerspective(*args: any, **kwargs: any) -> None: pass  # type: ignore
    def gluLookAt(*args: any, **kwargs: any) -> None: pass  # type: ignore


@dataclass
class TerrainMesh:
    """Represents a terrain mesh for rendering"""
    vertices: np.ndarray
    indices: np.ndarray
    normals: np.ndarray
    colors: np.ndarray
    vao: Optional[int] = None
    vbo: Optional[int] = None
    ebo: Optional[int] = None
    vertex_count: int = 0


class OpenGLRenderer:
    """GPU-accelerated terrain renderer using OpenGL"""
    
    def __init__(self, width: int = 1024, height: int = 768, use_shaders: bool = True):
        """
        Initialize the OpenGL renderer
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            use_shaders: Whether to use modern shader-based rendering
        """
        if not OPENGL_AVAILABLE:
            logger.warning("OpenGL libraries not available. Using fallback mode.")
            self.available = False
            self.width = width
            self.height = height
            self.use_shaders = use_shaders
            return
        
        self.available = True
        self.width = width
        self.height = height
        self.use_shaders = use_shaders
        self.shader_program = None
        self.meshes = {}
        self.display = None
        self.clock = None
        
        # Camera parameters
        self.camera_distance = 50.0
        self.camera_height = 30.0
        self.camera_angle_x = 35.0  # degrees
        self.camera_angle_y = 45.0  # degrees
        
        # Lighting
        self.light_position = np.array([100.0, 100.0, 100.0, 1.0])
        self.ambient_light = np.array([0.3, 0.3, 0.3, 1.0])
        self.diffuse_light = np.array([0.7, 0.7, 0.7, 1.0])
        self.specular_light = np.array([1.0, 1.0, 1.0, 1.0])
        
        logger.info(f"OpenGL Renderer initialized ({width}x{height})")
    
    def initialize(self):
        """Initialize OpenGL context and resources"""
        pygame.init()
        flags = DOUBLEBUF | OPENGL
        self.display = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("TerraSim OpenGL Renderer")
        self.clock = pygame.time.Clock()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        if self.use_shaders:
            self._compile_shaders()
        else:
            self._setup_fixed_pipeline()
        
        logger.info("OpenGL context initialized")
    
    def _compile_shaders(self):
        """Compile GLSL vertex and fragment shaders"""
        vertex_shader = """
        #version 120
        
        varying vec3 fragNormal;
        varying vec3 fragColor;
        varying vec3 fragPosition;
        
        void main() {
            fragNormal = normalize(gl_NormalMatrix * gl_Normal);
            fragColor = gl_Color.rgb;
            fragPosition = (gl_ModelViewMatrix * gl_Vertex).xyz;
            gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
        }
        """
        
        fragment_shader = """
        #version 120
        
        varying vec3 fragNormal;
        varying vec3 fragColor;
        varying vec3 fragPosition;
        
        uniform vec4 lightPos;
        uniform vec4 ambientLight;
        uniform vec4 diffuseLight;
        uniform vec4 specularLight;
        
        void main() {
            // Normalize interpolated normal
            vec3 norm = normalize(fragNormal);
            
            // Light direction
            vec3 lightDir = normalize(lightPos.xyz - fragPosition);
            
            // Ambient
            vec3 ambient = ambientLight.rgb * fragColor;
            
            // Diffuse
            float diff = max(dot(norm, lightDir), 0.0);
            vec3 diffuse = diff * diffuseLight.rgb * fragColor;
            
            // Specular
            vec3 viewDir = normalize(-fragPosition);
            vec3 reflectDir = reflect(-lightDir, norm);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
            vec3 specular = spec * specularLight.rgb;
            
            // Combine
            gl_FragColor = vec4(ambient + diffuse + specular, 1.0);
        }
        """
        
        try:
            vs = compileShader(vertex_shader, GL_VERTEX_SHADER)
            fs = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
            self.shader_program = compileProgram(vs, fs)
            logger.info("Shaders compiled successfully")
        except Exception as e:
            logger.error(f"Shader compilation failed: {e}")
            raise
    
    def _setup_fixed_pipeline(self):
        """Setup fixed-function pipeline (fallback for older systems)"""
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # Setup light 0
        glLight(GL_LIGHT0, GL_POSITION, self.light_position)
        glLight(GL_LIGHT0, GL_AMBIENT, self.ambient_light)
        glLight(GL_LIGHT0, GL_DIFFUSE, self.diffuse_light)
        glLight(GL_LIGHT0, GL_SPECULAR, self.specular_light)
        
        # Setup material properties
        glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)
        
        logger.info("Fixed-pipeline rendering setup")
    
    def create_terrain_mesh(
        self,
        dem: np.ndarray,
        name: str = "terrain",
        colormap: str = "viridis"
    ) -> TerrainMesh:
        """
        Create a terrain mesh from a DEM
        
        Args:
            dem: 2D array of elevation values
            name: Mesh name for storage
            colormap: Matplotlib colormap name for visualization
        
        Returns:
            TerrainMesh object
        """
        if not self.available:
            # Fallback: return empty mesh structure
            return TerrainMesh(
                vertices=np.array([]),
                indices=np.array([]),
                normals=np.array([]),
                colors=np.array([]),
                vertex_count=0
            )
        
        # Create vertex positions (3D)
        height, width = dem.shape
        x = np.linspace(0, width - 1, width)
        z = np.linspace(0, height - 1, height)
        xx, zz = np.meshgrid(x, z)
        yy = dem.copy()
        
        # Flatten for vertex array
        vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]).astype(np.float32)
        
        # Create face indices (triangles)
        indices = []
        for i in range(height - 1):
            for j in range(width - 1):
                v0 = i * width + j
                v1 = i * width + (j + 1)
                v2 = (i + 1) * width + j
                v3 = (i + 1) * width + (j + 1)
                
                indices.extend([v0, v1, v2])
                indices.extend([v1, v3, v2])
        
        indices = np.array(indices, dtype=np.uint32)
        
        # Calculate normals (per-vertex)
        normals = self._calculate_vertex_normals(vertices, indices, dem.shape)
        
        # Create colors based on elevation
        colors = self._create_elevation_colors(dem, colormap)
        colors_flat = np.column_stack([
            colors[:, :, 0].ravel(),
            colors[:, :, 1].ravel(),
            colors[:, :, 2].ravel(),
            np.ones(len(vertices))
        ]).astype(np.float32)
        
        mesh = TerrainMesh(
            vertices=vertices,
            indices=indices,
            normals=normals,
            colors=colors_flat,
            vertex_count=len(indices)
        )
        
        # Upload to GPU
        if self.use_shaders:
            self._upload_mesh_vao(mesh)
        
        self.meshes[name] = mesh
        logger.info(f"Created terrain mesh '{name}' with {len(vertices)} vertices")
        
        return mesh
    
    def _calculate_vertex_normals(
        self,
        vertices: np.ndarray,
        indices: np.ndarray,
        shape: Tuple[int, int]
    ) -> np.ndarray:
        """Calculate per-vertex normals"""
        normals = np.zeros_like(vertices)
        height, width = shape
        
        # Use Sobel-like gradient for normal calculation
        dem_2d = vertices[:, 1].reshape(shape)
        grad_x = np.gradient(dem_2d, axis=1)  # type: ignore
        grad_z = np.gradient(dem_2d, axis=0)  # type: ignore
        
        # Normal is perpendicular to surface
        for i in range(height):
            for j in range(width):
                idx = i * width + j
                normal = np.array([-grad_x[i, j], 1.0, -grad_z[i, j]])  # type: ignore
                norm = np.linalg.norm(normal)
                if norm > 1e-6:
                    normals[idx] = normal / norm
        
        return normals.astype(np.float32)
    
    def _create_elevation_colors(
        self,
        dem: np.ndarray,
        colormap: str = "viridis"
    ) -> np.ndarray:
        """Create RGB colors based on elevation"""
        try:
            import matplotlib.pyplot as plt  # type: ignore
            import matplotlib.cm as cm  # type: ignore
            
            cmap = cm.get_cmap(colormap)
            
            # Normalize elevation to [0, 1]
            dem_min, dem_max = dem.min(), dem.max()
            dem_normalized = (dem - dem_min) / (dem_max - dem_min + 1e-6)
            
            # Map to RGBA and extract RGB
            rgba = cmap(dem_normalized)
            rgb = np.asarray(rgba)[:, :, :3]  # type: ignore
            
            return rgb.astype(np.float32)
        except ImportError:
            # Fallback: use simple elevation-based coloring
            dem_min, dem_max = dem.min(), dem.max()
            normalized = (dem - dem_min) / (dem_max - dem_min + 1e-6)
            
            # Create viridis-like colormap
            rgb = np.zeros((*dem.shape, 3), dtype=np.float32)
            rgb[:, :, 0] = 0.267 + 0.4 * normalized  # Red channel
            rgb[:, :, 1] = 0.004 + 0.9 * (1 - np.abs(2 * normalized - 1))  # Green
            rgb[:, :, 2] = 0.329 + 0.5 * (1 - normalized)  # Blue channel
            
            return np.clip(rgb, 0, 1).astype(np.float32)
    
    def _upload_mesh_vao(self, mesh: TerrainMesh):
        """Upload mesh to GPU using VAO/VBO"""
        if not self.shader_program:
            return
        
        # Create VAO
        mesh.vao = glGenVertexArrays(1)
        glBindVertexArray(mesh.vao)
        
        # Create VBO for vertices
        mesh.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo)
        glBufferData(GL_ARRAY_BUFFER, mesh.vertices.nbytes, mesh.vertices, GL_STATIC_DRAW)
        
        # Vertex position attribute
        pos_loc = glGetAttribLocation(self.shader_program, "gl_Vertex")
        glVertexAttribPointer(pos_loc, 3, GL_FLOAT, False, 12, ctypes.c_void_p(0))
        glEnableVertexAttribArray(pos_loc)
        
        # Create EBO
        mesh.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, mesh.indices.nbytes, mesh.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
        logger.info("Mesh uploaded to GPU")
    
    def render_mesh(self, mesh_name: str = "terrain"):
        """Render a mesh"""
        if mesh_name not in self.meshes:
            logger.warning(f"Mesh '{mesh_name}' not found")
            return
        
        mesh = self.meshes[mesh_name]
        
        if self.shader_program and mesh.vao is not None:
            glUseProgram(self.shader_program)
            glBindVertexArray(mesh.vao)
            glDrawElements(GL_TRIANGLES, mesh.vertex_count, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            glUseProgram(0)
        else:
            # Fixed pipeline fallback
            glBegin(GL_TRIANGLES)
            for i in range(0, len(mesh.indices), 3):
                for j in range(3):
                    idx = mesh.indices[i + j]
                    glColor3fv(mesh.colors[idx, :3])
                    glVertex3fv(mesh.vertices[idx])
            glEnd()
    
    def update_mesh_colors(self, colors: np.ndarray, mesh_name: str = "terrain"):
        """Update mesh colors dynamically"""
        if mesh_name not in self.meshes:
            return
        
        mesh = self.meshes[mesh_name]
        expected_count = len(mesh.vertices)
        
        # Handle different color array dimensions
        if colors.ndim == 1:
            # Single channel - replicate across all channels
            if len(colors) != expected_count:
                logger.warning(f"Color array size {len(colors)} doesn't match vertex count {expected_count}")
                return
            r = g = b = colors
        elif colors.ndim == 2:
            # Grayscale 2D - replicate across channels
            if colors.size != expected_count:
                logger.warning(f"Color array size {colors.size} doesn't match vertex count {expected_count}")
                return
            r = g = b = colors.ravel()
        elif colors.ndim == 3:
            # 3D array (height, width, 3)
            if colors.shape[0] * colors.shape[1] != expected_count:
                logger.warning(f"Color array size {colors.shape[0] * colors.shape[1]} doesn't match vertex count {expected_count}")
                return
            r = colors[:, :, 0].ravel()
            g = colors[:, :, 1].ravel()
            b = colors[:, :, 2].ravel()
        else:
            logger.error(f"Unsupported color array dimensions: {colors.ndim}")
            return
        
        colors_flat = np.column_stack([
            r, g, b,
            np.ones(expected_count)
        ]).astype(np.float32)
        mesh.colors = colors_flat
    
    def set_camera(self, distance: float, height: float, angle_x: float, angle_y: float):
        """Set camera position and orientation"""
        self.camera_distance = distance
        self.camera_height = height
        self.camera_angle_x = angle_x
        self.camera_angle_y = angle_y
    
    def render_frame(self):
        """Render a frame"""
        glClear(int(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT))  # type: ignore
        
        # Setup projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.1, 1000.0)
        
        # Setup model-view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Position camera
        import math
        angle_rad_x = math.radians(self.camera_angle_x)
        angle_rad_y = math.radians(self.camera_angle_y)
        cam_x = self.camera_distance * math.cos(angle_rad_y)
        cam_z = self.camera_distance * math.sin(angle_rad_y)
        gluLookAt(cam_x, self.camera_height, cam_z, 0, 0, 0, 0, 1, 0)
        
        # Render all meshes
        for mesh_name in self.meshes:
            self.render_mesh(mesh_name)
        
        pygame.display.flip()
    
    def shutdown(self):
        """Cleanup and shutdown"""
        if self.display:
            pygame.quit()
        logger.info("OpenGL Renderer shutdown")
