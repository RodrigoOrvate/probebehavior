# probebehavior

Water maze probe tests aligned on the **first arrival at the empty goal**.

In a probe test the platform is gone. The first time the animal reaches its former location is the moment its
expectation is violated. Standard probe measures (time in the target quadrant, crossings, proximity, entropy) summarise
the whole test; strategy classifiers such as Rtrack are trained on trials that end at the platform. `probebehavior` splits
each probe at the first arrival and describes the search that follows.

## Measures

For each probe, with the default settings:

| Column | Meaning |
|---|---|
| `reached` | whether the animal entered the goal at all |
| `arrival_latency_s` | time of the first entry into the goal |
| `path_efficiency` | straight-line distance from the start to the goal edge divided by the path swum until arrival |
| `persistence` | fraction of the 15 s after arrival spent within 20 cm of the goal |
| `reentries` | entries into the goal in those 15 s, after the first |
| `first_stay_s` | time from arrival until the animal first leaves the 20-cm zone |
| `mean_distance` | mean distance to the goal in those 15 s |
| `speed` | path length in those 15 s divided by 15 s |
| `turning_deg_s` | mean absolute heading change per second while swimming, in those 15 s |
| `wall_latency_s` | time from arrival to the first entry into the wall band (outer 20% of the radius), within 30 s |
| `wall_censored` | true when the wall band was not reached within 30 s |
| `other_locations_visits` | visits to the goal location rotated by 90°, 180° and 270° (other quadrants), within 30 s |

Measures that need a full window after arrival are left empty when the probe ends first. Aligned curves (distance to
goal, distance to wall, speed) are returned on a 1-s grid from 5 s before to 30 s after arrival. All windows, radii and
the probe length are settings.

## Use

```python
import probebehavior as pa

arena = pa.read_rtrack_arena('arenas/day8.txt')          # or pa.Arena((0, 0), 100, (42.3, 37.6), 6)
metrics, curves = pa.measure(*pa.read_track('tracks/rat01_PT1.csv'), arena)
```

Many probes at once, from an Rtrack experiment table (`_TrackID`, `_Arena`, `_TrackFile`, plus any other columns):

```
probebehavior experiment.csv --out probes.csv --curves curves.csv
```

Tracks are delimited text with time (s) and x, y in the arena units; arenas use the Rtrack description
(`arena.bounds = circle cx cy r`, `goal = circle gx gy r`), so the same files serve both tools.

## Install and test

```
pip install -e ".[test]"
pytest
```
