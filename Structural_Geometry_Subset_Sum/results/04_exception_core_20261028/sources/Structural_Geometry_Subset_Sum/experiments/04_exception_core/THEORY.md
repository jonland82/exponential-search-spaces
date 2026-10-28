# One geometric core, several exceptional assignments

After exact target reductions and gcd normalization, write positive weights as
$u_i=Mp_i+r_i$, $p_i\ge0$. Choose a partition into core $K$ and exceptions $E$.
Let $R_-^K=\sum_{i\in K}\min(0,r_i)$ and
$R_+^K=\sum_{i\in K}\max(0,r_i)$. A solution satisfies

$$
Mq+s=v-\sum_{i\in E}u_ix_i,\qquad
q=\sum_{i\in K}p_ix_i,\quad s=\sum_{i\in K}r_ix_i.
$$

Since exceptional weights are positive, every shifted target is at most $v$.
Thus every core selection that can solve any shifted target has

$$
0\le q\le Q=\min\left(\sum_{i\in K}p_i,
\left\lfloor\frac{v-R_-^K}{M}\right\rfloor\right),\qquad
R_-^K\le s\le R_+^K.
$$

Build one exact table with height $H=Q+1$ and width
$W=R_+^K-R_-^K+1$. For core prefixes, use

$$
S_0=\{(0,0)\},\qquad
S_j=S_{j-1}\cup\{(q+p_j,s+r_j):(q,s)\in S_{j-1}\}.
$$

Discard $q>Q$: nonnegative quotients cannot return to the permitted range.
Every prefix residual lies in the global core residual strip, so signed-bitset
clipping is also safe. Update q rows in descending order; when $p_j=0$, each
row reads its pre-update value once, using the item at most once. Save prefix
rows only through their attainable q bound, for witness reconstruction.

Enumerate $2^{|E|}$ exceptional assignments with Gray-code sum updates. For
each shifted target $z$, query only

$$
\max\left(0,\left\lceil\frac{z-R_+^K}{M}\right\rceil\right)
\le q\le
\min\left(Q,\left\lfloor\frac{z-R_-^K}{M}\right\rfloor\right),
\qquad s=z-Mq.
$$

A reachable point reconstructs a core witness; combine it with the exceptional
assignment and lift original indices. NO requires a complete table and
exhaustion of every exceptional assignment. Interruption never proves NO.

The accounting form is

$$
T\le F+C_{\rm core}+2^{|E|}Q_{\rm query}+V.
$$

Here $F$ includes blind base/partition discovery, $C_{\rm core}$ is one table
construction, and $V$ includes witness reconstruction/verification. Bitset
updates depend on integer width, not unit-cost bit operations. Logical storage
is at most $(|K|+1)HW$ bit positions plus interpreter/reference overhead.

Implementation chooses largest absolute residuals as exceptions, stopping at
the first partition satisfying fixed size and work bounds, with at most nine
exceptions. This is a heuristic partition, not minimum deletion distance.
The algorithm extends the program's certified exception-to-core mechanism;
it does not introduce a new general subset-sum complexity bound.
