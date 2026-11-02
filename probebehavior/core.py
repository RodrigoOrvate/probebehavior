"""Align a water maze probe test on the first arrival at the empty goal and measure what the animal does next."""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Arena:
    """Circular pool and goal, in the same units as the track (usually cm)."""
    center: tuple
    radius: float
    goal: tuple
    goal_radius: float


@dataclass(frozen=True)
class Settings:
    zone_radius: float = 20.0       # zone around the goal used for persistence and first stay
    wall_fraction: float = 0.2      # outer fraction of the radius counted as the wall band
    short_window: float = 15.0      # seconds after arrival for persistence, re-entries, distance, speed and turning
    long_window: float = 30.0       # seconds after arrival for wall latency, visits to other locations and curves
    duration: float = 60.0          # probe length; samples after it are dropped
    curve_start: float = -5.0       # aligned curves, seconds relative to arrival
    turning_step: float = 0.5       # resampling step for turning
    moving_speed: float = 2.0       # speed above which heading changes count as turning
    partial_window: bool = False    # late arrivals: use the time left (at least min_window) instead of dropping the short-window measures
    min_window: float = 1.0


def entries(inside):
    """Number of outside-to-inside transitions."""
    inside = np.asarray(inside, bool)
    return int(np.sum(inside[1:] & ~inside[:-1]))


def turning_rate(t, x, y, step=0.5, moving_speed=2.0):
    """Mean absolute heading change per second (degrees/s), resampled every `step` s, while the animal is swimming."""
    tt = np.arange(t[0], t[-1], step)
    if len(tt) < 3:
        return np.nan
    dx, dy = np.diff(np.interp(tt, t, x)), np.diff(np.interp(tt, t, y))
    moving = np.hypot(dx, dy) / step > moving_speed
    change = np.abs(np.angle(np.exp(1j * np.diff(np.arctan2(dy, dx)))))
    both = moving[1:] & moving[:-1]
    return np.degrees(change[both]).sum() / (step * len(change)) if both.any() else np.nan


def rotated_goals(arena, angles=(90, 180, 270)):
    """The goal rotated around the pool centre: the equivalent locations in the other quadrants."""
    cx, cy = arena.center
    gx, gy = arena.goal[0] - cx, arena.goal[1] - cy
    out = []
    for a in np.radians(angles):
        out.append((cx + gx * np.cos(a) - gy * np.sin(a), cy + gx * np.sin(a) + gy * np.cos(a)))
    return out


def clean(t, x, y, duration):
    """Drop missing samples and samples after the probe ends."""
    t, x, y = (np.asarray(v, float) for v in (t, x, y))
    keep = np.isfinite(t) & np.isfinite(x) & np.isfinite(y) & (t <= duration)
    return t[keep], x[keep], y[keep]


def first_arrival(t, x, y, arena):
    """Index of the first sample inside the goal, or None if the animal never enters it."""
    inside = np.hypot(np.asarray(x) - arena.goal[0], np.asarray(y) - arena.goal[1]) <= arena.goal_radius
    return int(np.argmax(inside)) if inside.any() else None


def in_target_quadrant(x, y, arena):
    """Target quadrant centred on the goal (within 45° of the goal direction, seen from the pool centre), as in Rtrack."""
    cx, cy = arena.center
    phi = np.arctan2(np.asarray(y) - cy, np.asarray(x) - cx) - np.arctan2(arena.goal[1] - cy, arena.goal[0] - cx)
    return np.abs((phi + np.pi) % (2 * np.pi) - np.pi) <= np.pi / 4


def classic_measures(t, x, y, arena, settings=Settings()):
    """Standard probe measures for the whole probe and split at the first arrival (suffixes `_pre` and `_post`).

    `quadrant_pct`: % of time in the target quadrant; `proximity`: mean distance to the goal (Gallagher); `crossings`:
    entries into the goal (in `_post`, the re-entries after the first arrival); `thigmotaxis_pct`: % of time in the wall
    band; `duration_s`: length of the segment. Animals that never reach the goal have no `_post` segment.
    """
    t, x, y = clean(t, x, y, settings.duration)
    d = np.hypot(x - arena.goal[0], y - arena.goal[1])
    r = np.hypot(x - arena.center[0], y - arena.center[1])
    inside = d <= arena.goal_radius
    quad = in_target_quadrant(x, y, arena)
    wall = r >= arena.radius * (1 - settings.wall_fraction)
    i0 = first_arrival(t, x, y, arena)
    cut = len(t) if i0 is None else i0
    out = {}
    for suffix, part in (('', slice(None)), ('_pre', slice(0, cut)), ('_post', slice(cut, None))):
        n = len(t[part])
        ok = n >= 2
        out |= {f'quadrant_pct{suffix}': 100 * quad[part].mean() if ok else np.nan,
                f'proximity{suffix}': d[part].mean() if ok else np.nan,
                f'crossings{suffix}': entries(inside[part]) if ok else np.nan,
                f'thigmotaxis_pct{suffix}': 100 * wall[part].mean() if ok else np.nan,
                f'duration_s{suffix}': t[part][-1] - t[part][0] if ok else np.nan}
    return out


def measure(t, x, y, arena, settings=Settings()):
    """Measures of one probe aligned on the first arrival at the goal.

    Returns (metrics, curves). `metrics['reached']` is False when the animal never enters the goal; measures that need a
    full window after arrival are left out when the probe ends before the window does, unless `partial_window` is set, in
    which case the short-window measures use the time left (reported as `window_s`). `curves` holds distance to goal,
    distance to wall and speed on a 1-s grid from `curve_start` to `long_window` around arrival, or is None.
    """
    t, x, y = clean(t, x, y, settings.duration)
    s = settings
    d = np.hypot(x - arena.goal[0], y - arena.goal[1])
    r = np.hypot(x - arena.center[0], y - arena.center[1])
    step = np.hypot(np.diff(x), np.diff(y))
    inside = d <= arena.goal_radius
    if not inside.any():
        return {'reached': False}, None
    i0 = int(np.argmax(inside))
    t0 = t[i0]
    straight = max(np.hypot(x[0] - arena.goal[0], y[0] - arena.goal[1]) - arena.goal_radius, 1e-6)
    m = {'reached': True, 'arrival_latency_s': t0,
         'path_efficiency': min(straight / max(step[:i0].sum(), straight), 1.0)}

    win = s.short_window if t0 + s.short_window <= s.duration else s.duration - t0
    if win == s.short_window or (s.partial_window and win >= s.min_window):
        w = (t >= t0) & (t < t0 + win)
        left = np.flatnonzero(d[i0:] > s.zone_radius)
        m |= {'window_s': win,
              'persistence': (d[w] <= s.zone_radius).mean(),
              'reentries': entries(inside[w]),
              'first_stay_s': (t[i0 + left[0]] - t0) if len(left) else s.duration - t0,
              'mean_distance': d[w].mean(),
              'speed': step[w[:-1]].sum() / win,
              'turning_deg_s': turning_rate(t[w], x[w], y[w], s.turning_step, s.moving_speed)}

    curves = None
    if t0 + s.long_window <= s.duration:
        w = (t >= t0) & (t < t0 + s.long_window)
        wall = np.flatnonzero(r[w] >= arena.radius * (1 - s.wall_fraction))
        visits = 0
        for gx, gy in rotated_goals(arena):
            near = np.hypot(x[w] - gx, y[w] - gy) <= s.zone_radius
            visits += entries(near) + int(near[0])
        m |= {'wall_latency_s': (t[w][wall[0]] - t0) if len(wall) else s.long_window,
              'wall_censored': len(wall) == 0,
              'other_locations_visits': visits}
        grid = np.arange(s.curve_start, s.long_window, 1.0) + 0.5
        tc = t - t0
        curves = {'time_s': grid,
                  'distance_to_goal': np.interp(grid, tc, d, left=np.nan),
                  'distance_to_wall': np.interp(grid, tc, arena.radius - r, left=np.nan),
                  'speed': np.interp(grid, tc[1:], step / np.diff(t), left=np.nan)}
    return m, curves
