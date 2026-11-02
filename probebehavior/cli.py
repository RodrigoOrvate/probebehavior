"""Command line: probebehavior EXPERIMENT.csv --out results.csv [--curves curves.csv]"""
import argparse
from dataclasses import fields

from .batch import measure_experiment
from .core import Settings
from .io import read_rtrack_experiment


def main(argv=None):
    p = argparse.ArgumentParser(prog='probebehavior', description='Align water maze probe tests on the first arrival at the '
                                'empty goal and measure the search that follows.')
    p.add_argument('experiment', help='Rtrack-style experiment table (_TrackID, _Arena, _TrackFile, ...)')
    p.add_argument('--out', required=True, help='CSV with one row per probe')
    p.add_argument('--curves', help='optional CSV with the aligned curves')
    for f in fields(Settings):
        p.add_argument(f'--{f.name.replace("_", "-")}', type=float, default=f.default)
    a = p.parse_args(argv)
    settings = Settings(**{f.name: getattr(a, f.name) for f in fields(Settings)})
    metrics, curves = measure_experiment(read_rtrack_experiment(a.experiment), settings)
    metrics.to_csv(a.out, index=False)
    if a.curves:
        curves.to_csv(a.curves, index=False)
    print(f'{len(metrics)} probes, {int(metrics.reached.sum())} reached the goal -> {a.out}')


if __name__ == '__main__':
    main()
