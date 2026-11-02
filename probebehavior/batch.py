"""Run the measures over many probes, and export the part before the first arrival for Rtrack."""
import os

import pandas as pd

from .core import Settings, classic_measures, clean, first_arrival, measure
from .io import read_rtrack_arena, read_track


def measure_experiment(experiment, settings=Settings(), classic=True):
    """`experiment` is a table as returned by `read_rtrack_experiment`; extra columns are carried over to the results.

    Returns (metrics, curves): one row per probe (aligned measures, plus the classic ones when `classic` is true), and
    one row per probe and second for probes with a full long window.
    """
    rows, curves = [], []
    arenas = {}
    for rec in experiment.to_dict('records'):
        if rec['_Arena'] not in arenas:
            arenas[rec['_Arena']] = read_rtrack_arena(rec['_Arena'])
        track = read_track(rec['_TrackFile'])
        m, c = measure(*track, arenas[rec['_Arena']], settings)
        if classic:
            m |= classic_measures(*track, arenas[rec['_Arena']], settings)
        info = {k: v for k, v in rec.items() if k not in ('_Arena', '_TrackFile')}
        rows.append(info | m)
        if c is not None:
            curves.append(pd.DataFrame(c).assign(_TrackID=rec['_TrackID']))
    return pd.DataFrame(rows), (pd.concat(curves, ignore_index=True) if curves else pd.DataFrame())


def export_pre_arrival(experiment, out_dir, settings=Settings()):
    """Write each probe up to (and including) the first arrival as a new track, with an Rtrack experiment table.

    The part before the arrival is the trial-like part of a probe, where Rtrack's strategy calls apply. Probes that never
    reach the goal are written whole. Returns the path of the new experiment table.
    """
    os.makedirs(os.path.join(out_dir, 'tracks'), exist_ok=True)
    rows = []
    for rec in experiment.to_dict('records'):
        arena = read_rtrack_arena(rec['_Arena'])
        t, x, y = clean(*read_track(rec['_TrackFile']), settings.duration)
        i0 = first_arrival(t, x, y, arena)
        end = len(t) if i0 is None else i0 + 1
        name = f"tracks/{rec['_TrackID']}.csv"
        pd.DataFrame({'Time': t[:end], 'X': x[:end], 'Y': y[:end]}).to_csv(os.path.join(out_dir, name), index=False)
        rows.append(rec | {'_TrackFile': name, '_TrackFileFormat': 'raw.csv', 'reached': i0 is not None})
    path = os.path.join(out_dir, 'experiment_pre_arrival.csv')
    pd.DataFrame(rows).to_csv(path, index=False)
    return path
