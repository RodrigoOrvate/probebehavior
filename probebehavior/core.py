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


def measure(t, x, y, arena, settings=Settings()):
    """Measures of one probe aligned on the first arrival at the goal.

    Returns (metrics, curves). `metrics['reached']` is False when the animal never enters the goal; measures that need a
    full window after arrival are left out when the probe ends before the window does, unless `partial_window` is set, in
    which case the short-window measures use the time left (reported as `window_s`). `curves` holds distance to goal,
    distance to wall and speed on a 1-s grid from `curve_start` to `long_window` around arrival, or is None.
    """
    t, x, y = (np.asarray(v, float) for v in (t, x, y))
    keep = np.isfinite(t) & np.isfinite(x) & np.isfinite(y) & (t <= settings.duration)
    t, x, y = t[keep], x[keep], y[keep]
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
