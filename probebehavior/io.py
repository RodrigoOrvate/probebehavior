"""Readers for tracks and arenas. Rtrack formats are supported so that Rtrack users can run probebehavior on the same files."""
import os

import pandas as pd

from .core import Arena


def read_track(path, time='Time', x='X', y='Y', sep=','):
    """A track as three arrays (time in s, x and y in the arena units) from a delimited text file."""
    d = pd.read_csv(path, sep=sep)
    return d[time].to_numpy(float), d[x].to_numpy(float), d[y].to_numpy(float)


def read_rtrack_arena(path):
    """Arena from an Rtrack arena description (`arena.bounds = circle cx cy r`, `goal = circle gx gy r`)."""
    fields = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = (p.strip() for p in line.split('=', 1))
                fields[key] = value.split()
    for key in ('arena.bounds', 'goal'):
        if key not in fields or fields[key][0] != 'circle':
            raise ValueError(f'{path}: expected "{key} = circle x y r"')
    cx, cy, r = map(float, fields['arena.bounds'][1:4])
    gx, gy, gr = map(float, fields['goal'][1:4])
    return Arena((cx, cy), r, (gx, gy), gr)


def read_rtrack_experiment(path):
    """An Rtrack experiment table (_TrackID, _Arena, _TrackFile, ...) with paths resolved relative to the table."""
    e = pd.read_csv(path, dtype=str)
    missing = {'_TrackID', '_Arena', '_TrackFile'} - set(e.columns)
    if missing:
        raise ValueError(f'{path}: missing columns {sorted(missing)}')
    base = os.path.dirname(os.path.abspath(path))
    for col in ('_Arena', '_TrackFile'):
        e[col] = [p if os.path.isabs(p) else os.path.join(base, p) for p in e[col]]
    return e
