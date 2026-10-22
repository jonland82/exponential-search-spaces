# Certified Coverage of Exponential Search Spaces

**[Read the paper](https://jonland82.github.io/exponential-search-spaces/)** · [PDF](Certified_Coverage_of_Exponential_Search_Spaces.pdf) · [LaTeX source](Certified_Coverage_of_Exponential_Search_Spaces.tex)

An exact search may begin with $2^n$ possibilities. The paper asks what it would take to avoid examining them one by one: represent some states structurally, let a learned model propose regions for exact elimination, and combine others through exact summaries of paired groups.

The three mechanisms cover disjoint parts of the space. With structural coverage $k(n)$, certified learned coverage $a(n)\delta(n)$, and paired coverage $p(n)$, the explicit residual is

$$
r(n)=2^n-\underbrace{\bigl(k(n)+a(n)\delta(n)+p(n)\bigr)}_{C(n)}.
$$

Coverage has a cost. Let $P(n)$ account for structural discovery and learned proposals with verification, and $Q_{\mathrm{pair}}(n)$ for constructing and certifying paired summaries. In the paper's model,

$$
T(n)=P(n)+Q_{\mathrm{pair}}(n)+r(n)+\log_2 k(n).
$$

**The criterion:** if the overhead is polynomial, modeled runtime is polynomial exactly when the uncovered residual is polynomial:

$$
T(n)=\mathrm{poly}(n)\quad\Longleftrightarrow\quad C(n)=2^n-\mathrm{poly}(n).
$$

This explains why removing even 99.999% of an exponential space is asymptotically insufficient when that fraction stays fixed. Exact verification lets learning propose removals without risking correctness. Pairing is useful only if summaries can be built or reused cheaply: an explicit tree over $2^n$ states still needs $2^n-1$ merges.

The paper gives a criterion for this model. Finding such coverage at polynomial cost for a concrete problem remains the substantive challenge.
