"""Read-only reuse of the existing exact experiment primitives."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
original_search_path = list(sys.path)
try:
    for folder in ("Learned_Solvability_Subset_Sum", "Structural_Distance_Subset_Sum"):
        sys.path.insert(0, str(ROOT / folder))
    from advanced_features import lift_witness, reduce_instance
    from features import input_length
    from Learned_Solvability_Subset_Sum.run_pilot import independent_halves, independent_query, weights_for
    from structural_subset_sum import (Limits, _Budget, _Limit, _inputs, _mask_indices,
        _root_answer, solve, solve_bitset, solve_dfs, solve_mitm)
finally:
    sys.path[:] = original_search_path
