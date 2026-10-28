"""Instance geometry for the separate, calibrated completion-classifier study."""
from math import log1p
import sys
from time import perf_counter

from Structural_Geometry_Subset_Sum.budget import Meter
from Structural_Geometry_Subset_Sum.compat import ROOT
from Structural_Geometry_Subset_Sum.structures.large_base import detect

# Reuse existing code without changing any source protected by earlier freezes.
_search_path = list(sys.path)
try:
    sys.path.insert(0, str(ROOT / "Learned_Solvability_Subset_Sum"))
    from prospective_study import (CONFIG as LEGACY_CONFIG, feature_vectors,
        infer, limited_portfolio, new_weights, reference)
    from neighbor_experiment import calibrated_bundle, probabilities, score
    from geometric_experiment import feature_names
finally:
    sys.path[:] = _search_path


ARMS = ("baseline15", "geometry18", "doubling19")
POLICIES = ("cheap15", "matched15", "geometry18", "doubling19")
MODEL_FOR = dict(cheap15="baseline15", matched15="baseline15",
                 geometry18="geometry18", doubling19="doubling19")
GEOMETRY_NAMES = ("log1p_relative_residual_width", "log1p_feasible_aggregate_count",
                  "log1p_projected_dp_bits")
SCHEMAS = dict(baseline15=feature_names("baseline"),
    geometry18=feature_names("baseline")+list(GEOMETRY_NAMES),
    doubling19=feature_names("baseline")+list(GEOMETRY_NAMES)+["additive_doubling_distinct_weights"])


def geometry_features(weights, target):
    """Blind, gcd-normalized bounded discovery; never receives generator metadata."""
    started = perf_counter()
    meter = Meter(1_000_000)
    geometry, count = detect(weights, target, meter, maximum=24)
    values = ([0., 0., 0.] if geometry is None else
        [log1p((geometry.width-1)/geometry.base), log1p(geometry.q_count),
         log1p(geometry.dp_bits)])
    meter.tick(3)
    return dict(values=values, work=meter.work, seconds=perf_counter()-started,
        candidates=count, geometry=None if geometry is None else geometry.record(),
        exact_no=geometry is not None and geometry.q_count == 0)


def doubling_feature(weights):
    """Exact |A+A|/|A| for DISTINCT values, including a+a; not subset-sum support."""
    started = perf_counter()
    values = sorted(set(weights))
    sums = {a+b for i, a in enumerate(values) for b in values[i:]}
    n, m = len(weights), len(values)
    work = max(1, n*max(1, n.bit_length())) + m*(m+1) + 1
    return dict(value=len(sums)/m if m else 0., distinct=m, sumset_size=len(sums),
                work=work, seconds=perf_counter()-started)


def base_features(weights, target, kernel):
    vectors, work, seconds, reuse = feature_vectors(weights, target, kernel)
    return dict(values=vectors["hybrid"], work=work["hybrid"], reuse=reuse,
                recorded_feature_seconds=seconds["hybrid"])


def design(case, arm):
    values = list(case["base"]["values"])
    if arm != "baseline15":
        values += case["geometry"]["values"]
    if arm == "doubling19":
        values += [case["doubling"]["value"]]
    return values


def pending_after_shared_checks(case):
    return (case["kernel"]["status"] == "unresolved"
        and case["base"]["reuse"]["status"] == "unresolved"
        and not case["geometry"]["exact_no"])


def inference_work(arm):
    return 6*len(SCHEMAS[arm])+20
