"""Frozen, list-level transfer of gap-normalized conformal refinement to Note III.

Run from this directory: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python run_refinement.py
No upstream files are modified. Exact sums are labels and evaluation data only.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import platform
import random
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import beta
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'upstream' / 'subset-sum'))
from ml_experiment import all_sums, list_features, make_weights, PREFILTER_MODULI
from experiment import suffix_residues

OUT = ROOT / 'results'
PROTOCOL = {
    'version': 1, 'seed': 731029, 'alpha': 0.05,
    'cohorts': {'train': [16, 1200], 'calibration': [16, 500],
                'test': [16, 1000], 'unseen_n20': [20, 240]},
    'generator': 'Upstream make_weights; family independently equiprobable independent/paired; fresh lists',
    'target_rule': 'Uniform on integer [round(.30 sum(w)),round(.70 sum(w))] conditional on reachable residues mod 8,10,16,32',
    'outer_interval': '512 random witnessed subsets lower; min(1, product_j(c_j+1)/eligible_target_count) upper',
    'primary': {'model': 'HistGradientBoostingRegressor', 'max_iter': 200,
                'max_leaf_nodes': 15, 'learning_rate': .05,
                'min_samples_leaf': 20, 'l2_regularization': 1.0},
    'baselines': ['same-calibration midpoint', 'degree-2 ridge on density proxy, unique fraction, and analytic upper'],
    'calibration': 'Two one-sided gap-normalized scores; rank ceil((m+1)*(1-alpha/2)); no model tuning on calibration/test',
    'primary_evaluation': 'All fresh n16 test lists; empirical coverage, exact binomial CI, mean per-list fractional shrinkage, width, timing',
    'diagnostics': ['family-specific results', 'unseen n20 without recalibration',
                    'top 20% predicted fractional shrinkage; diagnostic, no conditional guarantee'],
    'independent_label_checks': '30 small brute-force cases; first 12 n16 test labels independently checked with integer bitset DP',
    'limits': 'Synthetic distribution; marginal statistical coverage only; no per-instance deterministic refinement; training/calibration labels are exact and costed',
}
FEATURES = list(list_features([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])) + [
    'lower', 'upper', 'width', 'log2_support', 'log2_multiplicity_count',
    'skewness', 'kurtosis', 'gcd',
]
DENSITY_FEATURES = ['log_density_proxy', 'unique_fraction', 'upper']


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def freeze():
    OUT.mkdir(exist_ok=True)
    path = ROOT / 'protocol.json'
    if path.exists():
        assert json.loads(path.read_text()) == PROTOCOL, 'Protocol changed; refuse to overwrite'
    else:
        dump(path, PROTOCOL)
    upstream = {}
    for p in sorted((ROOT / 'upstream').rglob('*')):
        if p.is_file() and '__pycache__' not in str(p):
            upstream[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    dump(OUT / 'provenance.json', {
        'source_repository': 'https://github.com/jonland82/exponential-search-spaces',
        'upstream_sha256': upstream, 'protocol_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'python': platform.python_version(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'sklearn': sklearn.__version__,
    })
    print('Protocol frozen before generating labels.', flush=True)


def support(weights):
    total = sum(weights)
    lo, hi = round(.30 * total), round(.70 * total)
    masks = [(m, suffix_residues(weights, m)[0]) for m in PREFILTER_MODULI]
    period = math.lcm(*PREFILTER_MODULI)
    allowed = [r for r in range(period) if all((mask >> (r % m)) & 1 for m, mask in masks)]
    size = sum((hi-r)//period - (lo-1-r)//period for r in allowed)
    assert size > 0
    return lo, hi, size


def make_record(split, index, n):
    rng = random.Random(f"refinement:{PROTOCOL['seed']}:{split}:{index}")
    family = rng.choice(['independent', 'paired'])
    weights = make_weights(n, family, rng)
    t0 = time.perf_counter()
    lo, hi, size = support(weights)
    counts = Counter(weights)
    k = math.prod(c + 1 for c in counts.values())
    witnessed = set()
    for _ in range(512):
        bits = rng.getrandbits(n)
        value = sum(w for j, w in enumerate(weights) if bits & (1 << j))
        if lo <= value <= hi:
            witnessed.add(value)
    lower, upper = len(witnessed) / size, min(1., k / size)
    t1 = time.perf_counter()
    features = list_features(weights)
    a = np.asarray(weights, dtype=float)
    z = (a-a.mean()) / max(float(a.std()), 1.)
    features.update(lower=lower, upper=upper, width=upper-lower,
                    log2_support=math.log2(size), log2_multiplicity_count=math.log2(k),
                    skewness=float(np.mean(z**3)), kurtosis=float(np.mean(z**4)),
                    gcd=float(math.gcd(*weights)))
    t2 = time.perf_counter()
    sums = all_sums(weights)
    numerator = sum(lo <= s <= hi for s in sums)
    q = numerator / size
    t3 = time.perf_counter()
    assert lower <= q + 1e-12 and q <= upper + 1e-12
    record = dict(split=split, index=index, n=n, family=family, weights=weights,
                  list_hash=hashlib.sha256(json.dumps(sorted(weights)).encode()).hexdigest(),
                  lo=lo, hi=hi, support_size=size, multiplicity_count=k,
                  witnessed_count=len(witnessed), reachable_target_count=numerator,
                  distinct_sum_count=len(sums), lower=lower, upper=upper, exact_q=q,
                  features=features, outer_seconds=t1-t0, feature_seconds=t2-t1,
                  exact_label_seconds=t3-t2)
    return record


def validate_small():
    rng = random.Random(PROTOCOL['seed'] + 100)
    for _ in range(30):
        weights = [rng.randint(1, 40) for _ in range(rng.randint(5, 10))]
        brute = {sum(w for w, bit in zip(weights, bits) if bit)
                 for bits in itertools.product([0, 1], repeat=len(weights))}
        assert brute == all_sums(weights)
        lo, hi, size = support(weights)
        allowed = [t for t in range(lo, hi+1)
                   if all((suffix_residues(weights, m)[0] >> (t % m)) & 1
                          for m in PREFILTER_MODULI)]
        assert len(allowed) == size
        assert set(range(lo, hi+1)).intersection(brute).issubset(set(allowed))


def independent_bitset_checks(rows):
    checks = []
    for row in rows[:12]:
        start = time.perf_counter()
        bits = 1
        for w in row['weights']:
            bits |= bits << w
        count = ((bits >> row['lo']) & ((1 << (row['hi']-row['lo']+1))-1)).bit_count()
        assert count == row['reachable_target_count']
        checks.append({'index': row['index'], 'reachable_count': count,
                       'seconds': time.perf_counter()-start})
    return checks


def generate():
    rows = []
    for split, (n, count) in PROTOCOL['cohorts'].items():
        path = OUT / f'{split}.jsonl'
        with path.open('w') as handle:
            for index in range(count):
                row = make_record(split, index, n)
                rows.append(row)
                handle.write(json.dumps(row, allow_nan=False) + '\n')
                if (index+1) % 100 == 0:
                    print(f'{split}: {index+1}/{count}', flush=True)
    hashes = [r['list_hash'] for r in rows]
    assert len(hashes) == len(set(hashes)), 'Duplicate lists would compromise split independence'
    return rows


def matrix(rows, names=FEATURES):
    return np.asarray([[r['features'][name] for name in names] for r in rows])


def quantities(rows):
    l = np.asarray([r['lower'] for r in rows])
    u = np.asarray([r['upper'] for r in rows])
    q = np.asarray([r['exact_q'] for r in rows])
    return l, u, q, u-l


def quantile(scores):
    m = len(scores)
    rank = math.ceil((m+1) * (1-PROTOCOL['alpha']/2))
    return float(np.sort(scores)[rank-1]) if rank <= m else math.inf


def calibrated_allowances(rows, p):
    l, u, q, width = quantities(rows)
    # Collapsed certified intervals have zero error and contribute zero scores.
    rho = np.divide(q-l, width, out=np.full(len(rows), .5), where=width > 0)
    minus = np.where(width > 0, np.maximum(p-rho, 0), 0.)
    plus = np.where(width > 0, np.maximum(rho-p, 0), 0.)
    return quantile(minus), quantile(plus)


def binomial_ci(k, n):
    return [0. if k == 0 else float(beta.ppf(.025, k, n-k+1)),
            1. if k == n else float(beta.ppf(.975, k+1, n-k))]


def summarize(records):
    n = len(records)
    covered = sum(r['covered'] for r in records)
    old = np.asarray([r['original_width'] for r in records])
    new = np.asarray([r['new_width'] for r in records])
    shrink = np.asarray([r['fractional_shrinkage'] for r in records])
    return dict(lists=n, covered=covered, coverage=covered/n,
                coverage_binomial_95_ci=binomial_ci(covered, n),
                mean_original_width=float(old.mean()), mean_new_width=float(new.mean()),
                mean_fractional_shrinkage=float(shrink.mean()),
                median_fractional_shrinkage=float(np.median(shrink)),
                min_fractional_shrinkage=float(shrink.min()),
                ratio_of_mean_widths_removed=float(1-new.mean()/old.mean()),
                prediction_mae=float(np.mean([r['prediction_absolute_error'] for r in records])),
                max_violation=float(max(r['violation'] for r in records)),
                lower_misses=sum(r['lower_miss'] for r in records),
                upper_misses=sum(r['upper_miss'] for r in records))


def evaluate(rows, p, allowances):
    cm, cp = allowances
    records = []
    for r, center in zip(rows, p):
        l, u, q = r['lower'], r['upper'], r['exact_q']
        width = u-l
        prediction = l + center*width
        a, b = max(l, prediction-cm*width), min(u, prediction+cp*width)
        new_width = b-a
        shrink = 1-new_width/width if width > 0 else 0.
        expected_width = width * (min(center, cm) + min(1-center, cp))
        assert abs(new_width-expected_width) < 1e-10
        assert -1e-10 <= new_width <= width+1e-10
        if width > 0:
            assert shrink+1e-10 >= max(0., 1-cm-cp)
        records.append(dict(split=r['split'], index=r['index'], family=r['family'],
                            n=r['n'], lower=l, upper=u, exact_q=q, normalized_prediction=float(center),
                            prediction=float(prediction), refined_lower=float(a), refined_upper=float(b),
                            original_width=width, new_width=float(new_width), fractional_shrinkage=float(shrink),
                            covered=bool(a-1e-12 <= q <= b+1e-12),
                            lower_miss=bool(q < a-1e-12), upper_miss=bool(q > b+1e-12),
                            violation=float(max(a-q, q-b, 0.)),
                            prediction_absolute_error=float(abs(prediction-q))))
    return records


def run():
    freeze()
    start = time.perf_counter()
    validate_small()
    rows = generate()
    cohorts = {s: [r for r in rows if r['split'] == s] for s in PROTOCOL['cohorts']}
    dump(OUT / 'independent_checks.json', independent_bitset_checks(cohorts['test']))
    train, cal = cohorts['train'], cohorts['calibration']
    l, u, q, width = quantities(train)
    y = np.divide(q-l, width, out=np.full(len(train), .5), where=width > 0)
    primary = HistGradientBoostingRegressor(**{k: v for k, v in PROTOCOL['primary'].items() if k != 'model'},
                                           random_state=PROTOCOL['seed'])
    density = make_pipeline(PolynomialFeatures(degree=2, include_bias=False),
                            StandardScaler(), Ridge(alpha=1.0))
    t0 = time.perf_counter()
    primary.fit(matrix(train), y)
    primary_train_seconds = time.perf_counter()-t0
    t0 = time.perf_counter()
    density.fit(matrix(train, DENSITY_FEATURES), y)
    density_train_seconds = time.perf_counter()-t0
    summary = {'protocol': PROTOCOL, 'features': FEATURES,
               'validation': {'small_bruteforce_cases': 30, 'independent_n16_bitset_cases': 12,
                              'no_duplicate_lists': True,
                              'all_outer_bounds_contain_truth': True,
                              'width_identity_and_shrinkage_inequality_checked_every_prediction': True},
               'models': {}, 'timing': {}}
    predictions = []
    for name in ['learned', 'density', 'midpoint']:
        def predict(items):
            if name == 'learned':
                return np.clip(primary.predict(matrix(items)), 0, 1)
            if name == 'density':
                return np.clip(density.predict(matrix(items, DENSITY_FEATURES)), 0, 1)
            return np.full(len(items), .5)
        t0 = time.perf_counter()
        cm, cp = calibrated_allowances(cal, predict(cal))
        calibration_seconds = time.perf_counter()-t0
        entry = {'c_minus': cm, 'c_plus': cp,
                 'pointwise_minimum_fractional_shrinkage': max(0., 1-cm-cp),
                 'calibration_prediction_and_quantile_seconds': calibration_seconds,
                 'cohorts': {}}
        for split in ['test', 'unseen_n20']:
            cohort = cohorts[split]
            t0 = time.perf_counter()
            p = predict(cohort)
            prediction_seconds = time.perf_counter()-t0
            records = evaluate(cohort, p, (cm, cp))
            for r in records:
                r['model'] = name
            predictions.extend(records)
            report = summarize(records)
            report['batched_prediction_seconds'] = prediction_seconds
            report['by_family'] = {f: summarize([r for r in records if r['family'] == f])
                                   for f in ['independent', 'paired']}
            selected = sorted(records, key=lambda r: (-r['fractional_shrinkage'], r['index']))[:math.ceil(.2*len(records))]
            report['top_20_percent_fractional_shrinkage_diagnostic'] = summarize(selected)
            entry['cohorts'][split] = report
        summary['models'][name] = entry
    for split, cohort in cohorts.items():
        summary['timing'][split] = {
            'lists': len(cohort),
            'total_outer_seconds': sum(r['outer_seconds'] for r in cohort),
            'total_feature_seconds': sum(r['feature_seconds'] for r in cohort),
            'total_exact_label_seconds': sum(r['exact_label_seconds'] for r in cohort),
            'median_outer_ms': float(1000*np.median([r['outer_seconds'] for r in cohort])),
            'median_feature_ms': float(1000*np.median([r['feature_seconds'] for r in cohort])),
            'median_exact_label_ms': float(1000*np.median([r['exact_label_seconds'] for r in cohort])),
        }
    summary['timing'].update(primary_fit_seconds=primary_train_seconds,
                             density_fit_seconds=density_train_seconds,
                             total_experiment_seconds=time.perf_counter()-start)
    with (OUT / 'predictions.csv').open('w', newline='') as h:
        writer = csv.DictWriter(h, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)
    dump(OUT / 'summary.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    run()
