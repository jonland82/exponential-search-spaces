"""Entry point for the frozen first structural-geometry experiment."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from Structural_Geometry_Subset_Sum.study import main

if __name__ == "__main__":
    main()
