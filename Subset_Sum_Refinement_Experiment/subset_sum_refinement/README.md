# Calibrated refinement test for Note III

Open Subset_Sum_Refinement_Report.html for the complete result.
Install requirements.txt, then run:

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python run_refinement.py
    python make_report.py

protocol.json was frozen before generating any labels. The primary test used
1,000 independent 16-item lists; the 240 20-item lists are a prespecified
size-transfer diagnostic. Sources are snapshots obtained through GitHub from
jonland82/exponential-search-spaces. No remote repository was modified.
The results directory contains exact labels, full weight lists, model
predictions, independent label checks, and SHA-256 provenance.
