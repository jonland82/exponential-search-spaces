"""Canonical paper locations; publication status is explicit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = (
    dict(number="I", folder="01-certified-coverage",
         stem="Certified_Coverage_of_Exponential_Search_Spaces",
         title="Certified Coverage of Exponential Search Spaces",
         description="A costed framework for certified coverage of exponential search spaces.",
         nav_label="Note I: Framework", data=None, published=True, maintained_html=True),
    dict(number="II", folder="02-subset-sum-stress-test",
         stem="Subset_Sum_as_a_Stress_Test",
         title="Subset Sum as a Stress Test for Certified Coverage",
         description="An experimental note testing exact pairing and learned proposals on subset sum.",
         nav_label="Note II: Exact-search stress test", data="subset-sum/README.md",
         published=True, maintained_html=False),
    dict(number="III", folder="03-probability-valued-subset-sum",
         stem="Probability_Valued_Subset_Sum",
         title="Probability-Valued Subset Sum: Certified Bounds and Learned Guidance",
         description="Certified range and collision bounds, calibrated tightening, and a prospective cost benchmark.",
         nav_label="Note III: Random-target probability",
         data="subset-sum/PROBABILITY_REFINEMENT.md", published=True, maintained_html=False),
    dict(number="IV", folder="04-certified-approximation",
         stem="Certified_Approximation_of_Subset_Sum",
         title="Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment",
         description="A controlled negative timing result for paired approximate subset-sum summaries.",
         nav_label="Note IV: Pairing in approximation",
         data="subset-sum/APPROXIMATION_RESULTS.md", published=True, maintained_html=False),
    dict(number="V", folder="05-structural-distance",
         stem="Structural_Distance_in_Subset_Sum",
         title="How Far from Easy? Structural Distance in Subset Sum",
         description="A working draft about tractable cores, residual sums, and the cost of selecting structure.",
         nav_label="Note V: Structural distance",
         data="Structural_Distance_Subset_Sum/FINDINGS.md", published=True,
         working_draft=True, maintained_html=False),
    dict(number="VI", folder="06-learned-solvability",
         stem="Predicting_Subset_Sum_Completion",
         title="Predicting Subset-Sum Completion: The Value and Cost of Structural Features",
         description="Five structural distances, calibrated completion prediction, paid prioritization, and certified branch-pruning experiments.",
         nav_label="Note VI: Learned completion",
         data="Learned_Solvability_Subset_Sum/README.md",
         published=True, maintained_html=False),
    dict(number="VII", folder="07-geometric-cores",
         stem="Geometric_Cores_and_Exceptions_in_Subset_Sum",
         title="Geometric Cores and Exceptions in Subset Sum",
         description="An exact geometric core route with fresh paid completion gains and a bounds-first construction ablation.",
         nav_label="Note VII: Geometric core reuse",
         data="Structural_Geometry_Subset_Sum/README.md",
         published=True, working_draft=True, maintained_html=False),
)


def directory(paper):
    return ROOT / "notes" / paper["folder"]


def artifact(paper, extension):
    return directory(paper) / (paper["stem"] + extension)
