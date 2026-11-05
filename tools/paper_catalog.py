"""Canonical paper locations; publication status is explicit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = (
    dict(number="I", folder="01-certified-coverage",
         stem="Certified_Coverage_of_Exponential_Search_Spaces",
         title="Certified Coverage of Exponential Search Spaces",
         description="Accounts for collectively represented or excluded candidates, residual search, and the full cost of acquiring and checking structure.",
         nav_label="Note I: Framework", data=None, published=True, maintained_html=True),
    dict(number="II", folder="02-subset-sum-stress-test",
         stem="Subset_Sum_as_a_Stress_Test",
         title="Subset Sum as a Stress Test for Certified Coverage",
         description="Tests exact pairing and learned proposals. Pairing adds overhead on the constructed hard NO cases; predictions still require verification.",
         nav_label="Note II: Exact-search stress test", data="subset-sum/README.md",
         published=True, maintained_html=False),
    dict(number="III", folder="03-probability-valued-subset-sum",
         stem="Probability_Valued_Subset_Sum",
         title="Probability-Valued Subset Sum: Certified Bounds and Learned Guidance",
         description="Bounds random-target reachability with range and collision certificates, then tests calibrated tightening and its transfer limits.",
         nav_label="Note III: Random-target probability",
         data="subset-sum/PROBABILITY_REFINEMENT.md", published=True, maintained_html=False),
    dict(number="IV", folder="04-certified-approximation",
         stem="Certified_Approximation_of_Subset_Sum",
         title="Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment",
         description="Compares paired and sequential summaries under a common accuracy rule, finding no consistent extra timing benefit from pairing.",
         nav_label="Note IV: Pairing in approximation",
         data="subset-sum/APPROXIMATION_RESULTS.md", published=True, maintained_html=False),
    dict(number="V", folder="05-structural-distance",
         stem="Structural_Distance_in_Subset_Sum",
         title="How Far from Easy? Structural Distance in Subset Sum",
         description="Finds maximum superincreasing cores and bounds residual work by exceptions or distinct sums. Core selection must repay its discovery cost.",
         nav_label="Note V: Structural distance",
         data="Structural_Distance_Subset_Sum/FINDINGS.md", published=True,
         working_draft=True, maintained_html=False),
    dict(number="VI", folder="06-learned-solvability",
         stem="Predicting_Subset_Sum_Completion",
         title="Predicting Subset-Sum Completion: The Value and Cost of Structural Features",
         description="Tests structural features for completion prediction, paid prioritization, and certified branch checks, retaining mixed results and acquisition costs.",
         nav_label="Note VI: Learned completion",
         data="Learned_Solvability_Subset_Sum/README.md",
         published=True, maintained_html=False),
    dict(number="VII", folder="07-geometric-cores",
         stem="Geometric_Cores_and_Exceptions_in_Subset_Sum",
         title="Geometric Cores and Exceptions in Subset Sum",
         description="Reuses an exact quotient–remainder table across exceptional assignments. Fresh constructed-input studies charge the full route cost.",
         nav_label="Note VII: Geometric core reuse",
         data="Structural_Geometry_Subset_Sum/README.md",
         published=True, working_draft=True, maintained_html=False),
)

# These are part of the research library without changing the numbered series
# or the existing main-paper build targets. Formats describe assets actually
# present in this checkout; the conservation manuscript currently has PDF only.
SUPPLEMENTS = (
    dict(key="conservation", kind="Standalone note", source_dir="notes/conservation-of-computational-work",
         stem="conservation_of_search_work", title="A Conservation Law for Search Work",
         description="Discovery/search tradeoffs, model-specific lower bounds, and pruning break-even costs.",
         formats=(".pdf",)),
    dict(key="clusters", kind="Companion to Note VI", source_dir="notes/06-learned-solvability",
         stem="Why_Unresolved_Inputs_Cluster",
         title="Why Unresolved Inputs Cluster: A Structural and Statistical Account",
         description="Solver routes and descriptive clustering of unresolved inputs.",
         formats=(".html", ".pdf", ".tex")),
    dict(key="geometric-runtime", kind="Companion to Note VII", source_dir="notes/07-geometric-cores",
         stem="Runtime_of_Geometric_Core_Subset_Sum",
         title="The Runtime of Geometric Core Subset Sum",
         description="Construction, query, and memory costs for exact geometric reuse.",
         formats=(".html", ".pdf", ".tex"), working_draft=True),
    dict(key="connections", kind="Connections paper", source_dir="OpenAI_Subset_Sum_Connections",
         stem="From_Choices_to_Sums",
         title="From Choices to Sums: Connections to OpenAI's Subset-Sum Algorithms",
         description="Distinct sums, compatible records, modular filtering, and shared core tables.",
         formats=(".html", ".pdf", ".tex")),
    dict(key="runtime-bands", kind="Standalone note", source_dir="OpenAI_Subset_Sum_Connections",
         stem="Runtime_Distribution_from_Structural_Routes",
         title="Why Subset-Sum Runtimes Form Several Bands",
         description="Runtime distributions as mixtures of solver routes and structural cost scales.",
         formats=(".pdf", ".tex")),
    dict(key="difficulty-buckets", kind="Standalone note", source_dir="notes/01-certified-coverage/distribution-shaping",
         stem="Distribution_Shaped_Difficulty_Buckets",
         title="Distribution-Shaped Difficulty Buckets",
         description="Chosen representation shapes and independently certified bucket mass and difficulty.",
         formats=(".pdf", ".tex"), working_draft=True),
)
ALL_PAPERS = PAPERS + SUPPLEMENTS


def paper_id(paper):
    return "note-" + paper["number"].lower() if "number" in paper else paper["key"]


def directory(paper):
    if paper.get("source_dir"):
        return ROOT / paper["source_dir"]
    return ROOT / "notes" / paper["folder"]


def artifact(paper, extension):
    return directory(paper) / (paper["stem"] + extension)
