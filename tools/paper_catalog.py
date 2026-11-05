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
    dict(key="block-overlap", kind="Standalone paper",
         source_dir="notes/01-certified-coverage/block-overlap",
         stem="Certified_Block_Overlap_in_Subset_Sum",
         title="Certified Block Overlap in Subset Sum",
         description="Bounds exact search by local overlap products and finds the best permitted contiguous blocks, with discovery costs included.",
         formats=(".pdf", ".tex"), working_draft=True),
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

# Editorial reading highlights, distinct from publication or evidence status.
CONCEPTUAL_HIGHLIGHTS = {
    "note-i": "The foundation: certified coverage and the cost of structure.",
    "conservation": "The foundation: account for discovery and residual search together.",
    "clusters": "The landscape: structural routes and the geography of unresolved cases.",
    "difficulty-buckets": "The synthesis: chosen geometry with independently checked difficulty.",
}

# Homepage highlights, transcribed from each manuscript. Captions retain the
# assumptions that distinguish models, exact algorithms and population claims.
KEY_EQUATIONS = {
    "block-overlap": (
        (r"\begin{gathered}\kappa_j=\max_z|S_j\cap[z-P_j,z]|\\K=\prod_j\kappa_j\end{gathered}",
         r"Each local overlap \(\kappa_j\) bounds surviving choices; their product \(K\) bounds complete search paths."),
        (r"T\le\operatorname{poly}(L)(2^b+K_b)",
         r"With at most \(b\) items per block, both discovery and exact search are paid; \(K_b\) is the optimal contiguous-partition product."),
    ),
    "note-i": (
        (r"r(n)=2^n-C(n)",
         r"Certified coverage \(C(n)\) leaves \(r(n)\) original candidates for explicit search."),
        (r"\begin{aligned}T(n)={}&P(n)+Q_{\mathrm{pair}}(n)\\&+r(n)+\rho(n,k(n))\end{aligned}",
         r"The model charges discovery \(P\), pairing \(Q_{\mathrm{pair}}\), residual search \(r\), and representation cost \(\rho\)."),
    ),
    "note-ii": (
        (r"\Sigma(A\cup B)=\Sigma(A)+\Sigma(B)",
         r"For disjoint item blocks, combining their attainable-sum sets is exact; constructing and querying those summaries still costs work."),
    ),
    "note-iii": (
        (r"q_\mu(w)=\sum_{t\in\mathcal A(w)\cap D}\mu(t)",
         r"Reachability probability is the mass of attainable targets under the specified target distribution \(\mu\)."),
        (r"\mu(L)\le q_\mu(w)\le\mu(U)",
         r"Witnessed targets \(L\) and the outer set \(U\) left by sound exclusions give deterministic probability bounds."),
    ),
    "note-iv": (
        (r"\begin{gathered}\ell\le d^*(w,t)\le u=|z-t|\\u-\ell\le\eta\end{gathered}",
         r"A witnessed sum \(z\) and certified lower bound \(\ell\) locate the optimal distance \(d^*\) within tolerance \(\eta\)."),
    ),
    "note-v": (
        (r"T=O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right)",
         r"With \(k(w)\) exceptions to a largest superincreasing core, discovery and exact enumeration take this many arithmetic/comparison operations."),
        (r"M(E)=|\mathcal A(E)|\le 2^{k(w)}",
         r"Merging equal exceptional sums reduces core queries to the \(M(E)\) distinct residual targets."),
    ),
    "note-vi": (
        (r"Y_B(x)=\mathbf1\!\left\{\substack{A(x)\text{ finishes exactly}\\\text{within its caps and }B(L_x)}\right\}",
         r"The label records exact completion within the fixed solver's resource allowance, whether the answer is YES or NO."),
        (r"\Pr_{X\sim\mathcal D}\!\left(Y_B(X)=1\mid\phi(X)=\phi(x)\right)",
         r"Features \(\phi(x)\) predict completion probability under input distribution \(\mathcal D\); their acquisition cost must also be paid."),
    ),
    "note-vii": (
        (r"\begin{aligned}S_0&=\{(0,0)\},\\S_j&=S_{j-1}\cup\bigl(S_{j-1}+(p_j,r_j)\bigr)\end{aligned}",
         r"Each core weight \(u_j=Mp_j+r_j\) updates the exact quotient–residual table, restricted to the proven safe bounds."),
        (r"Mq+s=T-\sum_{i\in A}u_i",
         r"Every exceptional selection \(A\) leaves a shifted target answered by the same core table."),
    ),
    "conservation": (
        (r"D_A(x_A)\ge\bigl[L(n)-S_A(x_A)\bigr]_+",
         r"On an algorithm's hard input \(x_A\), a proven worst-case lower bound \(L(n)\) limits how little discovery \(D_A\) can accompany search \(S_A\)."),
        (r"T_{\mathrm{prune}}<T_{\mathrm{base}}\iff bC>D",
         r"When each remaining check still costs \(b\), eliminating \(C\) candidates pays only if the saved work exceeds pruning cost \(D\)."),
    ),
    "clusters": (
        (r"\Pr(H'=1\mid H=1)=p+\frac{\operatorname{Var}(q(Z))}{p}",
         r"For conditionally independent failure labels sharing features \(Z\), varying local failure probability \(q(Z)\) creates enrichment above the overall rate \(p>0\)."),
    ),
    "geometric-runtime": (
        (r"\begin{aligned}T_{\mathrm{route}}&\le F+2^eB+ID+N_QQ_{\mathrm{pt}}+V,\\N_Q&\le 2^eG\end{aligned}",
         r"Pay discovery \(F\), per-assignment bounds \(B\), one table \(D\) when needed (\(I=1\)), at most \(G\) point tests per assignment, and verification \(V\)."),
        (r"T_{\mathrm{eager}}-T_{\mathrm{lazy}}=(1-I)D\ge0",
         r"For the same plan with sufficient resources, bounds-first construction saves the entire table cost when every assignment is rejected."),
    ),
    "connections": (
        (r"d(E)=e-\log_2|\mathcal A(E)|",
         r"Deficiency measures how much the distinct-sum support compresses the \(2^e\) selections of \(e\) exceptional items."),
        (r"T_V\le\operatorname{poly}(L)\,2^{e-d(E)}",
         r"With an exactly queryable superincreasing core, Note V's bit-cost bound depends on distinct exceptional sums and encoded input length \(L\)."),
    ),
    "runtime-bands": (
        (r"\begin{aligned}\Pr(Y\in A)&=\sum_{r\in\mathcal R}\pi_r\Pr(Y\in A\mid R=r)\\\pi_r&=\Pr(R=r)\end{aligned}",
         r"Elapsed time \(Y\) is an exact mixture over exit routes \(R\), including unresolved stops, whose eventual completion times remain unknown."),
    ),
    "difficulty-buckets": (
        (r"\begin{aligned}U&=F_g(S^-)+V\bigl[F_g(S)-F_g(S^-)\bigr],\\Z&=Q_g^{-1}(U)\end{aligned}",
         r"Within predicted group \(g\), randomized score ranks \(U\) map to a chosen CDF \(Q_g\), including truncated lognormal shapes."),
        (r"\Pr_{\mathrm{cal}}\!\left\{\begin{gathered}\forall b\in\widehat{\mathcal H}:\\\rho_b\ge\gamma,\quad p_b\ge1-\epsilon\end{gathered}\right\}\ge1-\delta",
         r"With training and reference fixed, independent calibration certifies mass \(\rho_b\) and hard-case purity \(p_b\) simultaneously for every reported hard bucket \(b\in\widehat{\mathcal H}\)."),
    ),
}


def paper_id(paper):
    return "note-" + paper["number"].lower() if "number" in paper else paper["key"]


def directory(paper):
    if paper.get("source_dir"):
        return ROOT / paper["source_dir"]
    return ROOT / "notes" / paper["folder"]


def artifact(paper, extension):
    return directory(paper) / (paper["stem"] + extension)
