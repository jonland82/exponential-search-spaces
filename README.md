# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers · September–October 2026

**[Read the series landing page](https://jonland82.github.io/exponential-search-spaces/)** · [Experiments and data](subset-sum/README.md)

This repository tells a short research story: a general criterion for avoiding explicit search over $2^n$ states, where $n$ is the number of binary choices; a subset-sum stress test that finds the limits of one implementation; a probability-valued question with certified bounds; and a fixed-target approximation question with a controlled distance gap. Each part is meant to stand alone.

| Note | Question | Read |
|---|---|---|
| **I. Certified Coverage of Exponential Search Spaces** | When can exact representation and certified exclusion leave only a polynomial residual? | [HTML](Certified_Coverage_of_Exponential_Search_Spaces.html) · [PDF](Certified_Coverage_of_Exponential_Search_Spaces.pdf) · [LaTeX](Certified_Coverage_of_Exponential_Search_Spaces.tex) |
| **II. Subset Sum as a Stress Test** | Do exact pairing, pruning, and learned proposals help on a concrete $2^n$ problem? | [HTML](Subset_Sum_as_a_Stress_Test.html) · [PDF](Subset_Sum_as_a_Stress_Test.pdf) · [LaTeX](Subset_Sum_as_a_Stress_Test.tex) |
| **III. Probability-Valued Subset Sum** | For a specified random target, how tightly can we bound the chance that it is reachable? | [HTML](Probability_Valued_Subset_Sum.html) · [PDF](Probability_Valued_Subset_Sum.pdf) · [LaTeX](Probability_Valued_Subset_Sum.tex) |
| **IV. Does Pairing Add Value to Certified Approximation?** | Does pairing add a computational benefit beyond the same approximation rule used sequentially? | [HTML](Certified_Approximation_of_Subset_Sum.html) · [PDF](Certified_Approximation_of_Subset_Sum.pdf) · [LaTeX](Certified_Approximation_of_Subset_Sum.tex) |

Read **I → II → III → IV** for the full narrative. Notes III and IV are sibling extensions of Note II: random-target probability and fixed-target approximation. Either branch can be read independently after I and II.

The first note counts only states handled by exact representations or certified exclusions. If $C(n)$ is that coverage, the explicit residual is

$$
r(n)=2^n-C(n).
$$

The cost of obtaining coverage matters. In the paper's model, polynomial coverage overhead yields polynomial runtime exactly when $r(n)$ is polynomially bounded. Note II tests that premise: the paired subset-sum solver was slower than meet-in-the-middle on all 18 constructed hard no-solution cases tested. A classifier ranked held-out cases, but even confident NO proposals included real YES cases.

Note III changes the objective. For a fixed list of weights $w=(w_1,\ldots,w_n)$, let $A(w)$ be its set of attainable subset sums. Draw a target $T$ from a stated distribution $\mu$. Then

$$
q_\mu(w)=\Pr_{T\sim\mu}[T\in A(w)].
$$

If $L$ contains witnessed reachable targets and $U$ contains every target not soundly excluded, write $\mu(B)$ for the probability that $T$ falls in a target set $B$. Then $\mu(L)\le q_\mu(w)\le\mu(U)$. These are certified bounds for a particular list; classifier probabilities are statistical estimates under the experiment's input distribution.

Note IV retains the motivation: "If we only need to get close to the target, and know how close, can our framework avoid much of the exponential search?" Its main contribution is a controlled negative timing result. With the same additive approximation rule and common greedy search disabled, pairing shows no consistent additional timing gain on the key jointly certified inputs. It finishes one additional input within the state cap. The [specification](subset-sum/APPROXIMATION_SPEC.md) supplies a common deterministic accuracy guarantee; the [experiment](subset-sum/APPROXIMATION_RESULTS.md) separates the effects of approximation, pairing, and early witness discovery. This limits the tested framework's demonstrated benefit from pairing while retaining the established usefulness of approximation.

## Reproduce the notes

- [subset-sum/README.md](subset-sum/README.md) links the exact-search benchmarks, classifier experiment, probability bounds, fixed-target approximation comparison, raw data, and figures.
- Run `python subset-sum/approximation_experiment.py` for the fixed-target tolerance sweep. Run `python -m unittest discover -s subset-sum -p test_certified_approximation.py -v` for independent checks of witnesses and bounds. Numerical experiments use the standard library; plots also require `matplotlib`.
- Run `python build_papers.py` to regenerate the three companion PDFs and HTML pages from their LaTeX sources. It requires `pdflatex` and `pandoc`.
- The original paper can be rebuilt with `pdflatex Certified_Coverage_of_Exponential_Search_Spaces.tex`. All HTML pages share [paper.css](paper.css).

These notes give a model criterion and results on small synthetic families. They do not claim a new worst-case subset-sum bound.
