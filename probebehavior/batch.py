"""Run `measure` over many probes and collect one row per probe plus the aligned curves."""
import pandas as pd

from .core import Settings, measure
from .io import read_rtrack_arena, read_track


def measure_experiment(experiment, settings=Settings()):
    """`experiment` is a table as returned by `read_rtrack_experiment`; extra columns are carried over to the results.

    Returns (metrics, curves): one row per probe, and one row per probe and second for probes with a full long window.
    """
    rows, curves = [], []
    arenas = {}
    for rec in experiment.to_dict('records'):
        if rec['_Arena'] not in arenas:
            arenas[rec['_Arena']] = read_rtrack_arena(rec['_Arena'])
        m, c = measure(*read_track(rec['_TrackFile']), arenas[rec['_Arena']], settings)
        info = {k: v for k, v in rec.items() if k not in ('_Arena', '_TrackFile')}
        rows.append(info | m)
        if c is not None:
            curves.append(pd.DataFrame(c).assign(_TrackID=rec['_TrackID']))
    return pd.DataFrame(rows), (pd.concat(curves, ignore_index=True) if curves else pd.DataFrame())
