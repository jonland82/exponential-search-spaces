"""Read-only audit of Stage 10 hashes, inputs, answers and accounting."""
import argparse
from collections import Counter
import json
from pathlib import Path

from branch_pruning import CONFIG, FROZEN, HERE, POLICIES, ROOT
from run_pilot import independent_halves, independent_query, sha


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def validate(output, *, oracle=True):
    manifest = json.loads((output / 'artifact_hashes.json').read_text())
    for name, digest in manifest.items():
        assert sha(output / name) == digest, ('artifact', name)
    protocol = json.loads((output / 'protocol.json').read_text())
    assert protocol['config'] == CONFIG
    for name, digest in protocol['sources'].items():
        assert sha(ROOT / name) == digest, ('current source', name)
        assert sha(output / 'sources' / name) == digest, ('snapshot source', name)
    assert protocol['model_sha256'] == sha(FROZEN / 'models.joblib')
    assert protocol['old_protocol_sha256'] == sha(FROZEN / 'protocol.json')
    cases = read(output / 'cases.jsonl')
    lists = read(output / 'lists.jsonl')
    assert len(cases) == 216 and len(lists) == 72
    assert len({tuple(sorted(row['weights'])) for row in lists}) == 72
    old = set()
    for path in HERE.glob('results/*/lists.jsonl'):
        if path.parent.resolve() != output.resolve():
            old.update(tuple(sorted(r['weights'])) for r in read(path))
    assert not old.intersection(tuple(sorted(r['weights'])) for r in lists)
    by_id = {c['case_id']: c for c in cases}
    assert len(by_id) == len(cases)
    for row in lists:
        group = [c for c in cases if c['list_id'] == row['list_id']]
        assert len(group) == 3
        halves = independent_halves(row['weights']) if oracle else None
        for case in group:
            assert case['weights'] == row['weights']
            mask = case['oracle_mask']
            assert case['truth'] == ('yes' if mask is not None else 'no')
            if mask is not None:
                assert sum(w for i, w in enumerate(case['weights']) if mask & (1 << i)) == case['target']
            if oracle:
                assert (independent_query(halves, case['target']) is not None) == (case['truth'] == 'yes')
        del halves
    runs = [r for path in sorted(output.glob('runs_*.jsonl')) for r in read(path)]
    assert len(runs) == 216 * len(POLICIES) * (1 + CONFIG['live_repeats'])
    identities = {(r['mode'], r['repeat'], r['policy'], r['case_id']) for r in runs}
    assert len(identities) == len(runs)
    for run in runs:
        case = by_id[run['case_id']]
        assert run['policy'] in POLICIES
        assert run['family'] == case['family'] and run['n'] == case['n']
        assert run['mode'] in ('nodes', 'live')
        assert run['counts']['checkpoints'] <= CONFIG['checkpoint_cap']
        assert run['counts']['core_queries'] <= 64 * run['counts']['structural_checks']
        assert run['counts']['structural_no'] + run['counts']['structural_yes'] <= run['counts']['structural_checks']
        assert run['counts']['structural_no_leaves'] <= 2**case['n']
        cap = CONFIG['deterministic_node_cap'] if run['mode'] == 'nodes' else CONFIG['live_node_cap']
        assert 0 <= run['counts']['nodes'] <= cap
        assert sum(run['component_seconds'].values()) <= run['seconds'] + 1e-8
        if run['status'] != 'unresolved':
            assert run['status'] == case['truth']
            if run['mode'] == 'live':
                assert run['seconds'] < CONFIG['live_seconds']
        if run['status'] == 'yes':
            witness = run['witness']
            assert len(witness) == len(set(witness))
            assert all(0 <= i < case['n'] for i in witness)
            assert sum(case['weights'][i] for i in witness) == case['target']
        else:
            assert run['witness'] is None
        if run['policy'] == 'dfs':
            assert run['counts']['structural_checks'] == 0
        if run['policy'] not in ('hybrid', 'conventional'):
            assert run['counts']['predictions'] == 0
    summary = json.loads((output / 'summary.json').read_text())
    for mode, policies in summary['by_mode'].items():
        for policy, item in policies.items():
            for repeat, saved in enumerate(item['repeats']):
                group = [r for r in runs if (r['mode'], r['policy'], r['repeat']) == (mode, policy, repeat)]
                assert len(group) == len(cases)
                assert saved['completed'] == sum(r['status'] != 'unresolved' for r in group)
                assert saved['total_nodes'] == sum(r['counts']['nodes'] for r in group)
                assert abs(saved['total_seconds'] - sum(r['seconds'] for r in group)) < 1e-8
    print(f"Validated {len(lists)} fresh lists, {len(cases)} truths, {len(runs)} runs, "
          f"all hashes/witnesses, limits and aggregates; oracle recheck={oracle}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--skip-oracle', action='store_true')
    args = parser.parse_args()
    validate(args.output, oracle=not args.skip_oracle)
