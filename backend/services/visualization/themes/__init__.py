"""
Theme modules for specialized visualization styles.
Provides domain-specific rendering themes (e.g., World Machine style).
"""

from .world_machine_style import (
    WorldMachineColorScheme,
    ErosionDepositionData,
    WorldMachineVisualizer,
    SimulationAnimationRenderer,
)

__all__ = [
    'WorldMachineColorScheme',
    'ErosionDepositionData',
    'WorldMachineVisualizer',
    'SimulationAnimationRenderer',
]
