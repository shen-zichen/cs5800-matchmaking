# 1 Introduction

## 1.1 Context

## 1.2 Problem Statement

# 2 Method

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

Feasibility is decided by reusing the Stage 2 (see §2.2) matching as an oracle: a window
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

## 2.2 Lane Matching (Stage 2)

Lane matching decides whether a set of players can be assigned to the five lanes using only lanes they are willing to play, and if so produces such an assignment. This is where **feasibility** lives: a match is role-complete only if every lane is staffed, so the question "can these players form a valid match?" reduces to "does a complete lane assignment exist?" We answer it by modeling the assignment as a **bipartite matching** (二分图匹配) and solving that matching as a **max-flow** (最大流) problem, following CLRS §26.3.

The construction places the players on one side and the five lanes on the other, and threads flow from a source through players and lanes to a sink. Formally we build a directed network $G = (V, E)$ with $V = \{s, t\} \cup P \cup L$, where $P$ is the player set and $L = \{\text{TOP}, \text{JUG}, \text{MID}, \text{ADC}, \text{SUP}\}$. There are three layers of edges. Each edge $(s, p_i)$ has capacity $1$, forcing every player to occupy at most one lane. Each edge $(p_i, \ell)$ has capacity $1$ and exists only when $\ell$ is player $p_i$'s primary or secondary preference — non-preferred lanes are simply absent, which is how "assign only within preference" is encoded structurally. Each edge $(\ell, t)$ has capacity $c$, bounding how many players a lane may hold.

The lane capacity $c$ is the one parameter that varies by caller. When the matcher assigns a single five-player team, $c = 1$: each lane takes exactly one player, and a max-flow of $5$ certifies a clean assignment. When it screens a ten-player pool — as the Stage 1 oracle does, and as lane-first (§2.4) does over the whole pool — $c = 2$: each lane must seat two players, one destined for each side, and a max-flow of $10$ certifies the pool can later split into two role-complete teams. In both cases the sink's total in-capacity is $5c$, so the flow is capped at $|P|$ by construction.

Reading the result is therefore direct: the pool is feasible **iff** its max-flow equals $|P|$, equivalently iff every lane edge into $t$ saturates. When flow falls short, the shortfall is exactly the number of players who could not be placed within preference, and we record it as $\text{autofill} = |P| - \text{max\_flow}$; these players are subsequently filled into whatever lanes remain open. Crucially, feasibility is read from the flow value alone and never from whether players ended up with an assigned lane — autofill assigns lanes even to infeasible pools, so an "everyone has a lane" check would report false feasibility (this is the red line the Stage 1 oracle depends on, §2.1).

**Hall's theorem** (霍尔定理) supplies the structural reason a pool passes or fails, complementing the numerical verdict max-flow returns. A perfect assignment exists iff for every subset $S$ of players, the lanes they collectively prefer, $N(S)$, satisfy $|N(S)| \ge |S|$ (in the capacitated form, $|N(S)| \cdot c \ge |S|$). A violated Hall condition — some group of players crowding onto too few lanes — is precisely what produces autofill, and it locates the bottleneck rather than merely counting it. The distinction worth keeping in view is that max-flow _computes_ the answer while Hall _explains_ it; tightening preferences makes the condition harder to satisfy, changing whether a solution exists, but never changes the polynomial cost of checking.

We solve the flow with **Edmonds-Karp** (BFS-based augmenting paths), whose $O(VE^2)$ bound is a small constant here since $V, E = O(n)$ with $n$ fixed at $5$ or $10$. This is the payoff for the thesis: because a feasibility check is one polynomial-time max-flow, and Stage 1 issues a linear number of such checks, establishing whether a role-complete match _can_ be formed is polynomial — the "feasibility is polynomial" half of §Thesis, standing opposite the NP-hardness of optimal balancing in §2.3.

One caveat is worth stating plainly, as the analysis in §2.4 leans on it. Because primary and secondary edges carry equal capacity $1$, the matcher does not _guarantee_ primary preferences are honored over secondary ones; when it happens to prefer primaries, that is an artifact of the BFS visiting primary edges first, not a property the model enforces. Enforcing genuine priority would require weighting the edges, which moves the problem to weighted assignment (out of scope; see §Limitations). We therefore treat all preferences as unweighted and report the primary-first tendency as an emergent behavior rather than a structural guarantee.

## 2.3 Team Balancing (Stage 3)

Team balancing takes the ten pooled players and splits them into two teams of
five, minimizing the difference in aggregate MMR between the sides. This is the
stage that makes a match _fair_: a small MMR gap means neither team is
predetermined to win before the game begins. Formally, writing the ten MMR
values as $w_1, \dots, w_{10}$, we seek a partition into $G_1, G_2$ with
$|G_1| = |G_2| = 5$ that minimizes
$\bigl|\sum_{i \in G_1} w_i - \sum_{i \in G_2} w_i\bigr|$.

We solve this by brute force. Because a match is fixed at ten players, there
are only $\binom{10}{5}/2 = 126$ distinct ways to cut the pool into two teams
of five — dividing by two because swapping the red and blue labels yields the
same partition — and we enumerate all of them, keeping the one with the
smallest gap. At this size the enumeration is instantaneous.

The reason this stage warrants discussion at all, rather than being a trivial
loop, is that the balancing problem is NP-complete _in general_, and it is only
the small, fixed instance size that lets us brute-force it. The rest of this
section makes that claim precise, as it is the theoretical core of the project
and the source of the "optimization is hard" half of our thesis (§Thesis). We
stress at the outset that NP-completeness is a _classification_ of the general
problem, not a statement about our ten-player instance; §2.3.4 returns to this
distinction.

### 2.3.1 The decision version

Complexity classes such as P and NP are defined over _decision_ problems —
those with a yes/no answer — because membership in NP is defined by
polynomial-time _verification_ of a candidate answer, which presupposes a
yes/no question. Our balancing objective is an optimization ("minimize the
gap"), so to classify its difficulty we first state its decision form:

> **BALANCE-DEC.** Given $2m$ MMR values $w_1, \dots, w_{2m}$ and a threshold
> $k$, does there exist a partition into two teams of exactly $m$ players each
> with $\bigl|\text{sum}_1 - \text{sum}_2\bigr| \le k$?

Membership in NP is immediate: a proposed partition serves as a certificate,
and verifying it — summing each side and comparing the difference to $k$ —
takes polynomial time. It remains to establish hardness.

### 2.3.2 NP-hardness: a reduction from PARTITION

We reduce from a classical NP-complete problem (CLRS §34.5):

> **PARTITION.** Given positive integers $S = \{a_1, \dots, a_n\}$ with total
> $T = \sum_i a_i$, does there exist a subset $A \subseteq S$ with
> $\text{sum}(A) = T/2$?

We show $\text{PARTITION} \le_p \text{BALANCE-DEC}$; since PARTITION is
NP-complete, this makes BALANCE-DEC NP-hard.

**Construction.** Given a PARTITION instance $S$, build a BALANCE-DEC instance
with $n$ _real_ players of MMR $a_1, \dots, a_n$ and $n$ _dummy_ players of
MMR $0$; set $m = n$ (teams of $n$) and $k = 0$. This is linear in $n$. The
dummy players are a gadget that reconciles the one structural mismatch between
the problems: PARTITION places no constraint on how many elements fall on each
side, whereas BALANCE-DEC forces the two teams to have _equal cardinality_. The
zero-valued dummies pad either team up to size $n$ without affecting its sum.

**Equivalence.** We show $S$ is a yes-instance of PARTITION if and only if the
constructed instance is a yes-instance of BALANCE-DEC.

$(\Rightarrow)$ Suppose $A \subseteq S$ with $\text{sum}(A) = T/2$, and let
$p = |A|$. Place the $p$ real players of $A$ on team one and pad with $n - p$
dummies; this team has $n$ players and sum $T/2$. The remaining $n - p$ real
players (summing to $T/2$) plus the remaining $p$ dummies form team two, also
of size $n$ and sum $T/2$. The gap is $0 \le k$, so BALANCE-DEC answers yes.
(The dummies suffice exactly: $(n - p) + p = n$ are used.)

$(\Leftarrow)$ Suppose the two teams $G_1, G_2$ each have $n$ players and
$\text{sum}_1 = \text{sum}_2$. Dummies contribute $0$, so each team's sum is
carried entirely by its real players; since the real total is $T$ and the two
sides are equal, the real players on $G_1$ sum to $T/2$. They therefore form a
subset of $S$ summing to $T/2$, so PARTITION answers yes. $\blacksquare$

Combining the two directions, $\text{PARTITION} \le_p \text{BALANCE-DEC}$, so
BALANCE-DEC is NP-hard. With membership in NP (§2.3.1), **BALANCE-DEC is
NP-complete.**

_Remark._ Because the teams are forced to equal size, adding any constant $C$
to all $2n$ MMR values raises each team's sum by $nC$ and leaves the gap
unchanged. The reduction thus goes through with strictly positive MMRs if
zero-valued players are deemed unrealistic — a small illustration that the
equal-cardinality constraint, far from being an obstacle, is what makes the
gadget clean.

### 2.3.3 The optimization version is NP-hard

Our implementation returns the _minimum_ gap, i.e. it solves the optimization
problem BALANCE-OPT, not the decision problem BALANCE-DEC. The hardness carries
over. An oracle that returns the minimum gap answers "is there a partition with
gap $\le k$?" with a single comparison, giving
$\text{BALANCE-DEC} \le_p \text{BALANCE-OPT}$; the optimization version is thus
at least as hard as the (NP-complete) decision version. BALANCE-OPT is,
moreover, _not known to be in NP_: verifying that a given partition achieves the
minimum gap appears to require comparison against all other partitions, so no
polynomial-time certificate is evident. We therefore classify BALANCE-OPT as
**NP-hard** rather than NP-complete.

### 2.3.4 Classification versus instance size

These results classify the _general_ problem, in which the player count is an
unbounded input; they state that there is _no known polynomial-time algorithm_
that balances arbitrarily large rosters optimally. They say nothing about any
particular instance. Our matches are fixed at ten players, so the search space
is a constant $126$ partitions and brute force is not merely feasible but
instantaneous. The justification for brute force is therefore the small
instance size, _not_ the NP-hardness: the classification and the tractability
of our instance are independent facts. (Compare the travelling-salesman
problem, which remains NP-complete even though a four-city instance is solvable
by hand.) This is precisely the two-sided structure of our thesis — feasibility
is polynomial (§2.2), optimal balancing is NP-hard in general (§2.3), and our
project is solvable only because each match is a small, fixed instance.

## 2.4 Two Orderings: Lane-first vs Balance-first

# 3 Experiment Setup

## 3.1 Synthetic Data Generation

## 3.2 Metrics

# 4 Analysis

## 4.1 Fairness–Preference Tradeoff

## 4.2 Scalability

# 5 Conclusion
