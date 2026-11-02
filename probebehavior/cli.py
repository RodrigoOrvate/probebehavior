"""Command line: probebehavior EXPERIMENT.csv --out results.csv [--curves curves.csv] [--export-pre-arrival DIR]"""
import argparse
from dataclasses import fields

from .batch import export_pre_arrival, measure_experiment
from .core import Settings
from .io import read_rtrack_experiment


def main(argv=None):
    p = argparse.ArgumentParser(prog='probebehavior', description='Align water maze probe tests on the first arrival at the '
                                'empty goal and measure the search that follows.')
    p.add_argument('experiment', help='Rtrack-style experiment table (_TrackID, _Arena, _TrackFile, ...)')
    p.add_argument('--out', required=True, help='CSV with one row per probe')
    p.add_argument('--curves', help='optional CSV with the aligned curves')
    p.add_argument('--no-classic', action='store_true', help='leave out the classic measures')
    p.add_argument('--export-pre-arrival', metavar='DIR', help='also write each probe up to the first arrival, for Rtrack')
    for f in fields(Settings):
        flag = f'--{f.name.replace("_", "-")}'
        if f.type in (bool, 'bool'):
            p.add_argument(flag, action='store_true')
        else:
            p.add_argument(flag, type=float, default=f.default)
    a = p.parse_args(argv)
    settings = Settings(**{f.name: getattr(a, f.name) for f in fields(Settings)})
    experiment = read_rtrack_experiment(a.experiment)
    metrics, curves = measure_experiment(experiment, settings, classic=not a.no_classic)
    metrics.to_csv(a.out, index=False)
    if a.curves:
        curves.to_csv(a.curves, index=False)
    print(f'{len(metrics)} probes, {int(metrics.reached.sum())} reached the goal -> {a.out}')
    if a.export_pre_arrival:
        print('pre-arrival tracks for Rtrack ->', export_pre_arrival(experiment, a.export_pre_arrival, settings))


if __name__ == '__main__':
    main()
