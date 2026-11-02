import pandas as pd
import pytest

from probebehavior import Settings, classic_measures, export_pre_arrival, measure_experiment, read_rtrack_experiment
from test_core import ARENA, FPS, track


def test_whole_pre_and_post_segments():
    # from the opposite side to the goal (arrives at x = 44, t = 9.4 s), then stays on it
    m = classic_measures(*track([(-50, 0), (50, 0), (50, 0)], [10, 50]), ARENA)
    assert m['duration_s_pre'] == pytest.approx(9.4, abs=1 / FPS)
    assert m['quadrant_pct_post'] == 100.0
    assert m['proximity_post'] < 1
    assert m['crossings'] == 1 and m['crossings_pre'] == 0 and m['crossings_post'] == 0
    assert m['thigmotaxis_pct'] == 0.0


def test_target_quadrant_is_centred_on_the_goal():
    m = classic_measures(*track([(30, 25), (30, 25)], [60]), ARENA)  # 40° from the goal direction
    assert m['quadrant_pct'] == 100.0
    m = classic_measures(*track([(20, 30), (20, 30)], [60]), ARENA)  # 56° from the goal direction
    assert m['quadrant_pct'] == 0.0


def test_never_reaching_leaves_post_empty_and_counts_the_wall():
    m = classic_measures(*track([(-90, 0), (-90, 30)], [60]), ARENA)
    assert m['quadrant_pct_post'] != m['quadrant_pct_post']  # NaN
    assert m['thigmotaxis_pct'] == 100.0 and m['thigmotaxis_pct_pre'] == 100.0


def test_export_cuts_at_arrival_and_runs_again(tmp_path):
    t, x, y = track([(-50, 0), (50, 0), (50, 0)], [10, 50])
    pd.DataFrame({'Time': t, 'X': x, 'Y': y}).to_csv(tmp_path / 'r1.csv', index=False)
    (tmp_path / 'a.txt').write_text('arena.bounds = circle 0 0 100\ngoal = circle 50 0 6\n')
    pd.DataFrame({'_TrackID': ['r1'], '_Arena': ['a.txt'], '_TrackFile': ['r1.csv']}).to_csv(tmp_path / 'e.csv', index=False)
    path = export_pre_arrival(read_rtrack_experiment(tmp_path / 'e.csv'), tmp_path / 'out')
    cut = pd.read_csv(tmp_path / 'out' / 'tracks' / 'r1.csv')
    assert cut.Time.iloc[-1] == pytest.approx(9.4, abs=1 / FPS)
    again, _ = measure_experiment(read_rtrack_experiment(path), Settings())
    assert bool(again.reached.iloc[0]) and again.arrival_latency_s.iloc[0] == pytest.approx(9.4, abs=1 / FPS)
