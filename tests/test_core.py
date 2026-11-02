import numpy as np
import pytest

from probebehavior import Arena, Settings, entries, measure, rotated_goals

ARENA = Arena((0.0, 0.0), 100.0, (50.0, 0.0), 6.0)
FPS = 30


def track(points, seconds):
    """Piecewise-linear path through `points`, each leg lasting the matching entry of `seconds`."""
    t, x, y, now = [], [], [], 0.0
    for (x0, y0), (x1, y1), dur in zip(points[:-1], points[1:], seconds):
        n = int(round(dur * FPS))
        f = np.arange(n) / n
        t += list(now + f * dur)
        x += list(x0 + f * (x1 - x0))
        y += list(y0 + f * (y1 - y0))
        now += dur
    return np.array(t + [now]), np.array(x + [points[-1][0]]), np.array(y + [points[-1][1]])


def test_never_reaching_goal():
    m, c = measure(*track([(-90, 0), (-90, 50)], [60]), ARENA)
    assert m == {'reached': False} and c is None


def test_arrival_latency_and_efficiency_of_a_straight_swim():
    m, _ = measure(*track([(-50, 0), (50, 0), (50, 0)], [10, 50]), ARENA)
    assert m['arrival_latency_s'] == pytest.approx((94 / 100) * 10, abs=1 / FPS)
    assert m['path_efficiency'] == pytest.approx(1.0, abs=0.01)


def test_staying_on_the_goal_gives_full_persistence_and_no_wall():
    m, c = measure(*track([(0, 0), (50, 0), (50, 0)], [5, 55]), ARENA)
    assert m['persistence'] == 1.0
    assert m['reentries'] == 0
    assert m['wall_censored'] and m['wall_latency_s'] == 30.0
    assert m['other_locations_visits'] == 0
    assert np.nanmax(c['distance_to_goal'][c['time_s'] > 1]) == pytest.approx(0, abs=1e-9)


def test_crossing_and_leaving_to_the_wall():
    # arrives at x = 44 (t = 4.4 s), leaves the 20-cm zone at x = 70 (t = 5.89 s), enters the wall band at x = 80 (6.33 s)
    m, _ = measure(*track([(0, 0), (50, 0), (95, 0), (95, 40)], [5, 2, 53]), ARENA)
    assert m['arrival_latency_s'] == pytest.approx(4.4, abs=1 / FPS)
    assert m['first_stay_s'] == pytest.approx(1.49, abs=0.05)
    assert m['wall_latency_s'] == pytest.approx(1.93, abs=0.05)
    assert m['persistence'] == pytest.approx(1.49 / 15, abs=0.01)
    assert not m['wall_censored']


def test_short_windows_are_dropped_when_the_probe_ends_first():
    m, c = measure(*track([(-50, 0), (50, 0), (50, 0)], [50, 10]), ARENA)
    assert m['reached'] and 'persistence' not in m and c is None


def test_rotated_goals_are_the_other_quadrants():
    got = np.round(rotated_goals(ARENA), 6)
    assert got.tolist() == [[0.0, 50.0], [-50.0, 0.0], [0.0, -50.0]]


def test_entries_counts_outside_to_inside_transitions():
    assert entries([False, True, True, False, True]) == 2


def test_settings_change_the_zone():
    t, x, y = track([(0, 0), (50, 0), (70, 0), (70, 0)], [5, 1, 54])
    narrow, _ = measure(t, x, y, ARENA, Settings(zone_radius=10))
    wide, _ = measure(t, x, y, ARENA, Settings(zone_radius=25))
    assert narrow['persistence'] < wide['persistence']
