2.3 team balancing · MD

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
