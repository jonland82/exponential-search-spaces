# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers · September 2026

**[Read the paper](https://jonland82.github.io/exponential-search-spaces/)** · [PDF](Certified_Coverage_of_Exponential_Search_Spaces.pdf) · [LaTeX source](Certified_Coverage_of_Exponential_Search_Spaces.tex)

An exact search over a problem of size $n$ may begin with $2^n$ candidate states. The paper asks what it would take to avoid examining them one by one: represent some states structurally, let a learned model propose regions for exact elimination, and combine others through summaries that preserve the search answer.

The three mechanisms cover disjoint parts of the space. Let $k(n)\ge1$ count structurally represented states, $\delta(n)$ count distinct states proposed for deletion, $a(n)\in[0,1]$ be the fraction certified safe by an exact verifier, and $p(n)$ count additional states represented by paired summaries. Their sum $C(n)$ is the total covered count; the number still searched individually is

$$
r(n)=2^n-\underbrace{\bigl(k(n)+a(n)\delta(n)+p(n)\bigr)}_{C(n)}.
$$

Coverage has a cost. Let $P(n)$ account for structural discovery and learned proposals with verification, and $Q_{\mathrm{pair}}(n)$ for constructing, certifying, and using paired summaries. Charging $\log_2 k(n)$ for the structural description and one unit per residual state, the modeled runtime is

$$
T(n)=P(n)+Q_{\mathrm{pair}}(n)+r(n)+\log_2 k(n).
$$

**The criterion:** if $P(n)+Q_{\mathrm{pair}}(n)$ is polynomially bounded, modeled runtime is polynomial exactly when the uncovered residual is polynomial. Here $\mathrm{poly}(n)$ means $O(n^d)$ for some fixed $d\ge0$:

$$
T(n)=\mathrm{poly}(n)\quad\Longleftrightarrow\quad C(n)=2^n-\mathrm{poly}(n).
$$

This explains why removing even 99.999% of an exponential space is asymptotically insufficient when that fraction stays fixed. Exact verification lets learning propose removals without risking correctness. Pairing is useful only if summaries can be built or reused cheaply: an explicit tree over $2^n$ states still needs $2^n-1$ merges.

The paper gives a criterion for this model. Finding such coverage at polynomial cost for a concrete problem remains the substantive challenge.
