## 2.1 Pooling (Stage 1)

A static snapshot may hold hundreds of queued players, and balancing teams
optimally over a set that large is intractable (the balancing problem is
NP-complete; see §2.3). Pooling reduces the snapshot to a small,
brute-forceable instance: a compact, lane-feasible 10-player pool $P$. We fix
$|P| = 10$ because a 5v5 match needs exactly ten players, and because holding
it constant lets the comparison experiment feed the _same_ ten players to
both orderings — isolating the ordering as the only variable. (The pool size
is parameterized, not hard-coded, so the scalability analysis in §X can grow
it.)

$P$ must be both **MMR-compact** (so teams can be balanced with a small gap)
and **lane-feasible** (assignable to the five lanes, two each, using only
preferred lanes). These can conflict, so pooling is a search: we sort the
snapshot by MMR (on a copy, leaving the caller's data untouched) and slide a
fixed-width window of 10 from lowest to highest, returning the first feasible
window. Sorting makes every contiguous window automatically MMR-compact, so
window position alone controls compactness.

Feasibility is decided by reusing the Stage 2 matching as an oracle: a window
is feasible iff its max-flow equals 10 (equivalently, autofill is zero). We
do _not_ inspect assigned lanes — autofill fills lanes even for infeasible
pools, faking feasibility.

Why a fixed window rather than growing one and letting max-flow pick 10 from
a larger set? Max-flow only certifies feasibility; its chosen ten ignore MMR
and may be scattered, breaking compactness. Recovering the most compact
feasible ten would mean searching $\binom{|W|}{10}$ subsets. A fixed window
keeps compactness built into the input instead of recovered afterward.

Sorting is $O(n\log n)$, the scan is $O(n)$ windows each needing one
polynomial-time max-flow — so the stage is polynomial, matching the
"feasibility is polynomial" half of our thesis.
