"""Paper VI geometry/pruning entry point after logical folder organization."""
import argparse
from pathlib import Path
import unittest
import sys

from threadpoolctl import threadpool_limits

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from Learned_Solvability_Subset_Sum.experiments._layout import EXPERIMENTS, PACKAGE, activate, audit_saved


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('experiment',choices=('geometric','pruning','all'))
    parser.add_argument('stage',choices=('check','audit','tests','freeze','generate','analyze','priorities'))
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.experiment=='all' and args.stage not in ('check','audit','tests'):
        parser.error('choose an individual experiment for a new run')
    if args.stage in ('freeze','generate','analyze','priorities') and args.output is None:
        parser.error('new experiment stages require --output with a fresh run directory')
    studies = activate()
    with threadpool_limits(limits=1):
        if args.stage=='tests':
            suite = unittest.TestSuite()
            for folder in (PACKAGE/'tests', EXPERIMENTS/'12_geometry/tests',
                    EXPERIMENTS/'13_feature_pruning/tests', EXPERIMENTS/'tests'):
                suite.addTests(unittest.TestLoader().discover(str(folder),pattern='test_*.py'))
            if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
                raise SystemExit(1)
            return
        for name in ('geometric','pruning') if args.experiment=='all' else [args.experiment]:
            output = args.output.resolve() if args.output else PACKAGE/f'results/{name}_20261028'
            if args.stage=='check':
                studies[name].verify(output)
                for manifest in ('data_hashes.json','prediction_hashes.json','priority_hashes.json'):
                    studies[name].check_hashes(output,manifest)
                print('Frozen sources, inputs and artifacts verified:',name,flush=True)
            elif args.stage=='audit':
                audit_saved(name,output)
            else:
                getattr(studies[name],args.stage)(output)


if __name__=='__main__':
    main()
