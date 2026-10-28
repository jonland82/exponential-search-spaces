# Independent audit correction

October 28, 2026. The initially frozen `validate_geometric.py` has an audit-only
variable-shadowing error. Its fresh-encoding loop reused `scale` for the scalar
encoding multiplier, overwriting the training standard-deviation vector captured
by the independent distance-reconstruction helper. The resulting fresh-distance
comparison correctly failed. The preceding independent centroid/model refits,
source/input checks and oracle replay had passed.

The corrected auditor is [audit_geometric.py](../../audit_geometric.py). Its
encoding loop uses `encoding_factor`, leaving the training scale vector intact.
It adds its own SHA-256 to `VALIDATION.json`. Its source is preserved separately
under `audit_sources/`. The initial auditor is retained byte-for-byte because it
is part of the original pre-generation source freeze.

No model, centroid, feature design, training/calibration split, protocol, input,
solver label, prediction, metric, timing or counter trace was changed. The
corrected auditor reruns the complete independent audit and deterministic replay;
this is a post-generation audit repair, not a new statistical analysis choice.

For validation, use the corrected command documented in this experiment's README.
