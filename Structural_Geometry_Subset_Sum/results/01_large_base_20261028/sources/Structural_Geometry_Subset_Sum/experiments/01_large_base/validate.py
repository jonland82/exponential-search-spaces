"""Read-only audit entry point for the saved first experiment."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from Structural_Geometry_Subset_Sum.audit import audit

if __name__ == "__main__":
    audit(Path(sys.argv[1]))
