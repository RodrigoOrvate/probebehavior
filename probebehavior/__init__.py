"""probebehavior: water maze probe tests aligned on the first arrival at the empty goal."""
from .batch import export_pre_arrival, measure_experiment
from .core import (Arena, Settings, classic_measures, clean, entries, first_arrival, in_target_quadrant, measure,
                   rotated_goals, turning_rate)
from .io import read_rtrack_arena, read_rtrack_experiment, read_track

__version__ = '0.1.1'
__all__ = ['Arena', 'Settings', 'measure', 'classic_measures', 'measure_experiment', 'export_pre_arrival', 'clean',
           'first_arrival', 'in_target_quadrant', 'entries', 'rotated_goals', 'turning_rate', 'read_track',
           'read_rtrack_arena', 'read_rtrack_experiment']
