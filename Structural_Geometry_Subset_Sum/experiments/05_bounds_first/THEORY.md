# Necessary bounds before exact geometric tables

The blind projection gives $w_i/d=M p_i+r_i$, $T=t/d$. Split indices into
a core $C$ and at most nine exceptions $E$. For an exceptional subset $A$,

$$
u_A=T-\sum_{i\in A}(Mp_i+r_i),\qquad
R_-=\sum_{i\in C}\min(0,r_i),\quad R_+=\sum_{i\in C}\max(0,r_i).
$$

Any core solution has $q=\sum_{i\in C}p_i x_i$ and
$R_-\le u_A-Mq\le R_+$. All $p_i\ge0$ and positive exceptional weights imply
that every required quotient fits the original cap

$$
Q=\min\left(\sum_{i\in C}p_i,\left\lfloor\frac{T-R_-}{M}\right\rfloor\right).
$$

Let $W_C=\sum_{i\in C}(Mp_i+r_i)$. Reject $A$ when $u_A\notin[0,W_C]$ or

$$
\max\left(0,\left\lceil\frac{u_A-R_+}{M}\right\rceil\right)
>
\min\left(Q,\left\lfloor\frac{u_A-R_-}{M}\right\rfloor\right).
$$

If every exceptional subset is rejected, this is an exact NO without a table.
A surviving interval does **not** establish YES: it may contain unreachable
$(q,r)$ pairs. Bounds-only returns unresolved; bounds-first builds the exact
table once, queries it, and reconstructs any witness from prefix tables.

For a fixed plan and sufficient resources, eager and lazy construction have
the same exact decisions. The lazy route saves construction precisely when
every assignment fails these bounds. If an assignment survives, it pays the
same table and query work as the matched eager control. In the counter model,

$$
C_{\rm eager}=F+B+C_{\rm table}+Q_{\rm points}+V,\qquad
C_{\rm lazy}=F+B+\mathbf1\{\text{some assignment survives bounds}\}
C_{\rm table}+Q_{\rm points}+V.
$$

Here $F$ includes paid discovery, $B$ assignment/bound checks and $V$ witness
verification. Bounds can use up to $2^{|E|}$ assignments. Interrupted enumeration
cannot certify NO. These are implementation costs with heterogeneous units,
not a new worst-case complexity result. Logical bit caps do not equal Python RSS.
