# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers · September–October 2026

**[Read the series landing page](https://jonland82.github.io/exponential-search-spaces/)** · [Experiments and data](subset-sum/README.md)

This repository tells a short research story: a general criterion for avoiding explicit search over $2^n$ states, a subset-sum stress test that finds the limits of one implementation, and a probability-valued question with certified bounds. Each part is meant to stand alone.

| Note | Question | Read |
|---|---|---|
| **I. Certified Coverage of Exponential Search Spaces** | When can exact representation and certified exclusion leave only a polynomial residual? | [HTML](Certified_Coverage_of_Exponential_Search_Spaces.html) · [PDF](Certified_Coverage_of_Exponential_Search_Spaces.pdf) · [LaTeX](Certified_Coverage_of_Exponential_Search_Spaces.tex) |
| **II. Subset Sum as a Stress Test** | Do exact pairing, pruning, and learned proposals help on a concrete $2^n$ problem? | [HTML](Subset_Sum_as_a_Stress_Test.html) · [PDF](Subset_Sum_as_a_Stress_Test.pdf) · [LaTeX](Subset_Sum_as_a_Stress_Test.tex) |
| **III. Probability-Valued Subset Sum** | For a specified random target, how tightly can we bound the chance that it is reachable? | [HTML](Probability_Valued_Subset_Sum.html) · [PDF](Probability_Valued_Subset_Sum.pdf) · [LaTeX](Probability_Valued_Subset_Sum.tex) |

The first note counts only states handled by exact representations or certified exclusions. If $C(n)$ is that coverage, the explicit residual is

$$
r(n)=2^n-C(n).
$$

The cost of obtaining coverage matters. In the paper's model, polynomial coverage overhead yields polynomial runtime exactly when $r(n)$ is polynomially bounded. Note II tests that premise: the paired subset-sum solver was slower than meet-in-the-middle on all 18 constructed hard no-solution cases tested. A classifier ranked held-out cases, but even confident NO proposals included real YES cases.

Note III changes the objective. For fixed weights $w$, reachable-sum set $A(w)$, and a target $T$ drawn from a stated distribution $\mu$,

$$
q_\mu(w)=\Pr_{T\sim\mu}[T\in A(w)].
$$

Witnessed sums $L$ and soundly admissible targets $U$ give $\mu(L)\le q_\mu(w)\le\mu(U)$. These are certified bounds for a particular list; classifier probabilities are statistical estimates under the experiment's input distribution.

## Reproduce the notes

- [subset-sum/README.md](subset-sum/README.md) links the exact-search benchmarks, classifier experiment, probability-bound experiment, raw data, and figures.
- Run `python build_papers.py` to regenerate the two companion PDFs and HTML pages from their LaTeX sources. It requires `pdflatex` and `pandoc`.
- The original paper can be rebuilt with `pdflatex Certified_Coverage_of_Exponential_Search_Spaces.tex`. All HTML pages share [paper.css](paper.css).

These notes give a model criterion and results on small synthetic families. They do not claim a new worst-case subset-sum bound.
