"""Repeat frozen audits while preserving their original exclusive-write records."""
import argparse
import json
from pathlib import Path

from Structural_Geometry_Subset_Sum.audit import audit as primary_audit
from Structural_Geometry_Subset_Sum.time_sensitivity import audit as sensitivity_audit


def preserve_record(auditor, output, record):
    """Both frozen auditors publish VALIDATION.json only after all checks pass."""
    try:
        auditor(output)
    except FileExistsError as exc:
        if exc.filename is None or Path(exc.filename).resolve() != record.resolve():
            raise
        assert json.loads(record.read_text())["status"] == "passed"
        print(f"All checks passed; original validation record preserved: {record}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sensitivity", action="store_true")
    args = parser.parse_args()
    preserve_record(primary_audit, args.output, args.output / "VALIDATION.json")
    if args.sensitivity:
        preserve_record(sensitivity_audit, args.output, args.output / "sensitivity_32L_live/VALIDATION.json")
