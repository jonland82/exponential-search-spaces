"""Regression, protocol freeze, and prospective deterministic-bound study.

python run_study.py regression
python run_study.py freeze
python run_study.py prospective
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import platform
from pathlib import Path
import random
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone

from bounds import (Targets, collision_terms, collision_upper, count_pairs,
                    decision, exact_bitset_count, exact_histogram, exact_set_count,
                    half_sums, original_interval, residue_cap, sampling_checkpoint,
                    selected_differences, study_targets, support_interval)


ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'subset_sum_refinement' / 'results'
OUT = ROOT / 'results'
METHODS = ['original', 'range', 'moment_cap', 'partial_8', 'partial_32',
           'residue_cap', 'combined']
PROTOCOL = {
    'version': 1, 'seed': 2026102302,
    'sizes': [12, 16, 20, 22], 'families': ['independent', 'paired'],
    'lists_per_size_family': 20,
    'generator': 'Unchanged formula from the preserved upstream make_weights; new seed strings',
    'targets': 'Uniform middle 40% integer interval, conditional on attainable residues mod 8,10,16,32',
    'witness_budget': 512, 'methods': METHODS,
    'differences': 'Common adjacent half-sum gaps, descending product of gap frequencies; integer gap tie break',
    'partial_budgets': [8, 32], 'representation_moduli': [16, 64],
    'representation_cap': 'Minimum basic cap and residue-wise sum-of-minima matching caps',
    'sampling': {'checkpoints': [128, 512, 2048], 'familywise_alpha': .05,
                 'band': 'Hoeffding, alpha/3 at each checkpoint, intersect original certified interval',
                 'decisions': 'Exact half-sum membership; all preprocessing charged'},
    'bitset_max_bits': 100_000_000,
    'exact_set': 'Positive-weight DP truncated at upper target, from scratch',
    'tolerances': [.05, .10, .20],
    'memory': 'Separate tracemalloc runs for first list of each stratum and every method; includes preprocessing; excludes interpreter baseline',
    'timing': 'One untraced standalone run per method and list; reproducibly shuffled order within certificate and oracle groups; no preprocessing reused',
    'truth': 'Full truncated set DP on every fresh list; compare bitset where feasible; truth evaluated after certificates',
    'disjointness': 'No repeated sorted weights within study or across any original cohort',
    'scope': 'Fixed deterministic algorithms plus exact-decision sampling; no learned extension or new calibration fit',
    'acceptance': 'All deterministic intervals contain integer truth; regression aggregates match transcript; independently checked proof implementation',
}
PROTECTED = ['bounds.py', 'run_study.py', 'test_bounds.py', 'THEOREM.md']


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_weights(weights):
    return hashlib.sha256(json.dumps(sorted(weights)).encode()).hexdigest()


def interval_record(lo, hi, d, seconds, **extra):
    return dict(lower_count=lo, upper_count=hi, denominator=d,
                lower=lo/d, upper=hi/d, width=(hi-lo)/d,
                total_seconds=seconds, **extra)


def calculate(weights, seed, method, existing=None):
    """Standalone method: includes support, witnesses, halves, and certificates."""
    start = time.perf_counter()
    targets = study_targets(weights)
    support_seconds = time.perf_counter()-start
    if existing is None:
        lower, upper, k = original_interval(weights, targets, random.Random(seed))
    else:
        lower, upper, k = existing
    base_seconds = time.perf_counter()-start
    d = targets.size
    if method == 'original':
        return interval_record(lower, upper, d, time.perf_counter()-start,
                               support_seconds=support_seconds, K=k)
    blocks, a, b = half_sums(weights)
    half_seconds = time.perf_counter()-start-base_seconds
    m = count_pairs(a, b, targets, all_pairs_pass_residues=True)
    assert m <= len(a)*len(b) <= k
    cap, j_lower, terms, residue_details = min(len(a), len(b)), 0, [], []
    if method in ('partial_8', 'partial_32', 'combined'):
        budget = 8 if method == 'partial_8' else 32
        differences = selected_differences(a, b, budget)
        terms = list(collision_terms(a, b, targets, differences, True))
        j_lower = sum(count for _, count in terms)
    if method in ('residue_cap', 'combined'):
        cap, residue_details = residue_cap(a, b, tuple(PROTOCOL['representation_moduli']))
    j_upper = collision_upper(m, cap)
    if method == 'range':
        lo, hi = lower, min(upper, m)
    else:
        lo, hi = support_interval(m, j_lower, j_upper, cap, d, lower, upper)
    return interval_record(lo, hi, d, time.perf_counter()-start,
                           K=k, M=m, J_lower=j_lower, J_upper=j_upper, R=cap,
                           half_sizes=[len(a), len(b)], partition=blocks,
                           collision_terms=terms, residue_caps=residue_details,
                           support_seconds=support_seconds, base_seconds=base_seconds,
                           half_seconds=half_seconds)


def sample_method(weights, seed):
    start = time.perf_counter()
    targets = study_targets(weights)
    lo, hi, _ = original_interval(weights, targets, random.Random(seed))
    _, a, b = half_sums(weights)
    if len(a) > len(b):
        a, b = b, a
    b_set = set(b)
    rng = random.Random(f'{seed}:sample-targets')
    successes, checkpoints = 0, []
    settings = PROTOCOL['sampling']
    for trial in range(1, max(settings['checkpoints'])+1):
        target = targets.sample(rng)
        successes += decision(target, a, b_set)
        if trial in settings['checkpoints']:
            r = sampling_checkpoint(successes, trial, targets.size, lo, hi,
                                    settings['familywise_alpha']/len(settings['checkpoints']))
            r['total_seconds'] = time.perf_counter()-start
            checkpoints.append(r)
    return checkpoints


def oracle_method(weights, method):
    start = time.perf_counter()
    targets = study_targets(weights)
    if method == 'exact_set':
        count = exact_set_count(weights, targets)
    elif method == 'bitset':
        count = exact_bitset_count(weights, targets, PROTOCOL['bitset_max_bits'])
    else:
        raise ValueError(method)
    return {'count': count, 'denominator': targets.size,
            'total_seconds': time.perf_counter()-start,
            'status': 'bit_cap_exceeded' if count is None else 'ok'}


def regression():
    OUT.mkdir(exist_ok=True)
    rows = [json.loads(line) for line in (OLD/'test.jsonl').read_text().splitlines()]
    output = []
    for index, row in enumerate(rows):
        weights, d, truth = row['weights'], row['support_size'], row['reachable_target_count']
        existing = row['witnessed_count'], min(d, row['multiplicity_count']), row['multiplicity_count']
        methods = {name: calculate(weights, '', name, existing) for name in METHODS}
        blocks, a, b = half_sums(weights)
        start = time.perf_counter()
        hist, m, j = exact_histogram(a, b, study_targets(weights))
        oracle_seconds = time.perf_counter()-start
        assert len(hist) == truth and m == methods['range']['M']
        for result in methods.values():
            assert result['denominator'] == d
            assert result['lower_count'] <= truth <= result['upper_count']
            if 'J_lower' in result:
                assert result['J_lower'] <= j <= result['J_upper']
                assert max(hist.values(), default=0) <= result['R']
        exact_cap = max(hist.values(), default=1)
        lo, hi = support_interval(m, j, j, exact_cap, d, existing[0], existing[1])
        methods['full_collision_oracle'] = interval_record(lo, hi, d, oracle_seconds,
                                                          M=m, J=j, R=exact_cap)
        output.append({'index': row['index'], 'list_hash': row['list_hash'],
                       'family': row['family'], 'n': row['n'], 'weights': weights,
                       'truth_count': truth, 'denominator': d, 'methods': methods})
        if (index+1) % 100 == 0:
            print(f'Regression {index+1}/{len(rows)}', flush=True)
    write_jsonl(OUT/'regression.jsonl', output)
    summary = summarize(output)
    measured = summary['overall']['range']
    assert measured['strictly_narrower'] == 778
    assert abs(measured['mean_width']-.372926981391316) < 1e-12
    assert abs(measured['mean_fractional_shrinkage']-.13098753580857592) < 1e-12
    assert all(v['covered'] == len(output) for v in summary['overall'].values())
    summary['transcript_reproduced'] = True
    summary['timing_note'] = 'Regression reuses stored witnessed counts; timings exclude their original construction. Full-collision method is an evaluation oracle.'
    dump(OUT/'regression_summary.json', summary)
    print(json.dumps(summary['overall'], indent=2), flush=True)


def freeze():
    path = ROOT/'protocol.json'
    frozen = {'protocol': PROTOCOL,
              'source_sha256': {name: sha(ROOT/name) for name in PROTECTED},
              'upstream_generator_sha256': sha(OLD.parent/'upstream/subset-sum/ml_experiment.py'),
              'frozen_at_utc': datetime.now(timezone.utc).isoformat()}
    if path.exists():
        check_freeze()
        print('Existing frozen protocol verified; not overwritten.')
    else:
        assert not (OUT/'prospective_weights.jsonl').exists()
        dump(path, frozen)
        print('Protocol and source hashes frozen before fresh-list generation.')


def check_freeze():
    frozen = json.loads((ROOT/'protocol.json').read_text())
    assert frozen['protocol'] == PROTOCOL, 'Protocol changed after freeze'
    assert frozen['source_sha256'] == {name: sha(ROOT/name) for name in PROTECTED}, 'Frozen source changed'
    assert frozen['upstream_generator_sha256'] == sha(OLD.parent/'upstream/subset-sum/ml_experiment.py')


def make_weights(n, family, rng):
    # Formula copied unchanged from the preserved upstream generator.
    multiplicity = 1 if family == 'independent' else 2
    effective_bits = (n//multiplicity)*math.log2(multiplicity+1)
    scale = max(32, round(2**(effective_bits+rng.uniform(-4, 4))))
    low = max(1, scale//4)
    unique = [rng.randint(low, scale) for _ in range(n//multiplicity)]
    weights = [weight for weight in unique for _ in range(multiplicity)]
    rng.shuffle(weights)
    return weights


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, allow_nan=False)+'\n')


def profile_memory(weights, seed):
    results = {}
    for name in METHODS+['sampling', 'exact_set', 'bitset']:
        gc.collect()
        tracemalloc.start()
        try:
            if name == 'sampling':
                result = sample_method(weights, seed)
            elif name in ('exact_set', 'bitset'):
                result = oracle_method(weights, name)
            else:
                result = calculate(weights, seed, name)
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        results[name] = {'peak_traced_bytes': peak,
                         'status': result.get('status', 'ok') if isinstance(result, dict) else 'ok'}
    return results


def prospective():
    check_freeze()
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'prospective.jsonl').exists(), 'Refuse to overwrite prospective evidence'
    old_hashes = set()
    for split in ('train', 'calibration', 'test', 'unseen_n20'):
        old_hashes.update(json.loads(line)['list_hash'] for line in (OLD/f'{split}.jsonl').read_text().splitlines())
    fresh, seen = [], set(old_hashes)
    for n in PROTOCOL['sizes']:
        for family in PROTOCOL['families']:
            for index in range(PROTOCOL['lists_per_size_family']):
                seed = f"deterministic:{PROTOCOL['seed']}:{n}:{family}:{index}"
                weights = make_weights(n, family, random.Random(seed))
                digest = digest_weights(weights)
                assert digest not in seen, 'Duplicate fresh or original instance'
                seen.add(digest)
                fresh.append(dict(n=n, family=family, index=index, seed=seed,
                                  weights=weights, list_hash=digest))
    # No labels have been computed when the complete manifest is saved.
    write_jsonl(OUT/'prospective_weights.jsonl', fresh)
    provenance = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
                  'protocol_sha256': sha(ROOT/'protocol.json'),
                  'weights_sha256': sha(OUT/'prospective_weights.jsonl'),
                  'python': platform.python_version(), 'platform': platform.platform(),
                  'original_lists_checked_for_overlap': len(old_hashes),
                  'original_data_sha256': {p.name: sha(p) for p in OLD.glob('*.jsonl')}}
    dump(OUT/'prospective_provenance.json', provenance)
    rows = []
    start = time.perf_counter()
    with (OUT/'prospective.jsonl').open('w', encoding='utf-8') as handle:
        for number, source in enumerate(fresh):
            row = dict(source)
            weights, seed = row['weights'], row['seed']
            order = METHODS+['sampling']
            random.Random(seed+':method-order').shuffle(order)
            methods = {}
            for name in order:
                if name == 'sampling':
                    samples = sample_method(weights, seed)
                else:
                    methods[name] = calculate(weights, seed, name)
            # Evaluation labels are obtained only after all tested intervals.
            oracle_order = ['exact_set', 'bitset']
            random.Random(seed+':oracle-order').shuffle(oracle_order)
            oracles = {name: oracle_method(weights, name) for name in oracle_order}
            truth = oracles['exact_set']['count']
            if oracles['bitset']['count'] is not None:
                assert oracles['bitset']['count'] == truth
            d = oracles['exact_set']['denominator']
            for result in methods.values():
                assert result['lower_count'] <= truth <= result['upper_count']
                assert result['denominator'] == d
            for result in samples:
                result['covered'] = result['lower'] <= truth/d <= result['upper']
            row.update(method_order=order, methods=methods, sampling=samples,
                       truth_count=truth, denominator=d, oracles=oracles)
            if row['index'] == 0:
                row['memory'] = profile_memory(weights, seed)
            handle.write(json.dumps(row, allow_nan=False)+'\n')
            handle.flush()
            rows.append(row)
            if (number+1) % 10 == 0:
                print(f'Prospective {number+1}/{len(fresh)}; n={row["n"]}, {row["family"]}', flush=True)
    summary = summarize(rows)
    summary['study_wall_seconds_including_memory_profiling'] = time.perf_counter()-start
    summary['unique_fresh_lists'] = len(seen)-len(old_hashes)
    summary['bitset_exact_agreements'] = sum(r['oracles']['bitset']['count'] is not None for r in rows)
    summary['bitset_skipped'] = sum(r['oracles']['bitset']['count'] is None for r in rows)
    summary['sampling'] = {}
    for trials in PROTOCOL['sampling']['checkpoints']:
        values = [next(x for x in r['sampling'] if x['trials'] == trials) for r in rows]
        summary['sampling'][str(trials)] = {
            'covered': sum(v['covered'] for v in values), 'lists': len(values),
            'mean_width': statistics.mean(v['width'] for v in values),
            'median_total_ms': 1000*statistics.median(v['total_seconds'] for v in values),
            'empty_intersections': sum(v['empty'] for v in values),
        }
    dump(OUT/'prospective_summary.json', summary)
    provenance['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    provenance['results_sha256'] = sha(OUT/'prospective.jsonl')
    dump(OUT/'prospective_provenance.json', provenance)
    check_freeze()
    print(json.dumps(summary, indent=2), flush=True)


def summarize(rows):
    def group_summary(group):
        result = {}
        for name in group[0]['methods']:
            values = [r['methods'][name] for r in group]
            original = [r['methods']['original']['width'] for r in group]
            widths = [v['width'] for v in values]
            result[name] = dict(
                lists=len(group), covered=sum(v['lower_count'] <= r['truth_count'] <= v['upper_count']
                                              for v, r in zip(values, group)),
                strictly_narrower=sum(w < o-1e-15 for w, o in zip(widths, original)),
                mean_width=statistics.mean(widths), median_width=statistics.median(widths),
                mean_fractional_shrinkage=statistics.mean(1-w/o if o else 0. for w, o in zip(widths, original)),
                ratio_of_mean_widths_removed=1-statistics.mean(widths)/statistics.mean(original),
                median_total_ms=1000*statistics.median(v['total_seconds'] for v in values),
                mean_total_ms=1000*statistics.mean(v['total_seconds'] for v in values),
            )
        return result
    return {'overall': group_summary(rows),
            'strata': {f'n{n}_{family}': group_summary([r for r in rows if r['n'] == n and r['family'] == family])
                       for n, family in sorted({(r['n'], r['family']) for r in rows})}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['regression', 'freeze', 'prospective'])
    args = parser.parse_args()
    globals()[args.stage]()
