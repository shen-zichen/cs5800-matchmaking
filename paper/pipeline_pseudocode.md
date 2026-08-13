# MOBA Matchmaking — Pipeline Pseudocode

> **One program, one pipeline.** The top-level `MATCHMAKING-PIPELINE` calls the
> three stage procedures and the two ordering procedures in turn (like a CLRS
> main procedure calling subroutines). This file states **algorithm logic only**;
> engineering details (defensive copy, import paths, reading the `matching` dict
> vs. `p.assigned_lane`, etc.) are **excluded** — they are not algorithms.
>
> **CLRS edition**: `<!-- TODO: standardize on 3rd ed (§26.3, max-flow in Ch 26) or 4th ed (Ch 24) -->`
> The paper, slides, and both members' pseudocode must agree.
> **Ownership**: `POOL` / `BALANCE-PARTITION` / `BALANCE-FIRST` by Zichen;
> `LANE-MATCH` (Stage 2) and `LANE-FIRST` / 32-split by Liuyi.
> Match the
> style of this file (CLRS indented).


---

## Top-level Pipeline

```
MATCHMAKING-PIPELINE(snapshot, ordering)
    P = POOL(snapshot)
    if P == NIL
        return "no feasible match"          // e.g. no feasible window under extreme preference concentration
    if ordering == LANE-FIRST
        return LANE-FIRST(P)
    else                                     // ordering == BALANCE-FIRST
        return BALANCE-FIRST(P)
```

---

## Stage 1 — Pooling _(Zichen)_

```
POOL(snapshot)                               // return an MMR-compact, lane-feasible 10-player pool
    sorted = SORT-BY-MMR(COPY(snapshot))     // sort on a copy (ascending); leave caller's data untouched
    n = |sorted|
    for i = 1 to n - 9                        // fixed width-10 window, sliding low MMR -> high
        W = sorted[i .. i+9]                  // 10 contiguous players => automatically MMR-compact
        (_, _, flow) = LANE-MATCH(W, cap = 2) // reuse Stage 2 as the feasibility oracle
        if flow == 10                         // RED LINE: feasible iff max-flow == 10,
            return W                          //           never "does everyone have an assigned_lane"
    return NIL                                // no width-10 window is lane-feasible
```

> **Why a fixed 10-window and not picking 10 from a larger one**: max-flow's
> feasible 10-set is non-unique and ignores MMR; letting it pick from a large
> window breaks compactness, and recovering it rigorously means searching
> C(|W|,10) subsets. A fixed window keeps compactness built into the input.

---

## Stage 2 — Lane Matching _(Liuyi)_

### LANE-MATCH

```
LANE-MATCH(P, cap)                           // max-flow bipartite lane matching (Edmonds-Karp)
    // Complexity: O(V * E^2) theoretically (Edmonds-Karp); O(1) in practice for fixed |P| (5 or 10)
    // Step 1: Construct flow network G = (V, E)
    G = CREATE-EMPTY-FLOW-NETWORK()
    for each player p in P
        ADD-DIRECTED-EDGE(G, s, p, cap = 1)
        ADD-DIRECTED-EDGE(G, p, p.pref_primary, cap = 1)    // Primary edge added first for implicit preference priority
        if p.pref_secondary != NIL
            ADD-DIRECTED-EDGE(G, p, p.pref_secondary, cap = 1)

    for each lane in {TOP, JUG, MID, ADC, SUP}
        ADD-DIRECTED-EDGE(G, lane, t, cap = cap)

    // Step 2: Edmonds-Karp main loop (push flow along BFS augmenting paths)
    max-flow = 0
    path = FIND-AUGMENTING-PATH-BFS(G, s, t)
    while path != NIL
        for each (u, v) in path
            G.flow(u, v) = G.flow(u, v) + 1  // forward edge flow +1
            G.flow(v, u) = G.flow(v, u) - 1  // backward residual edge flow -1 (undo mechanism)
        max-flow = max-flow + 1
        path = FIND-AUGMENTING-PATH-BFS(G, s, t)

    // Step 3: Extract matching results and calculate autofill gap
    matching = empty dict
    unmatched = empty list
    for each player p in P
        if G.flow(p, p.pref_primary) == 1
            matching[p.id] = p.pref_primary
        else if p.pref_secondary != NIL and G.flow(p, p.pref_secondary) == 1
            matching[p.id] = p.pref_secondary
        else
            unmatched.append(p)

    autofill = |P| - max-flow
    if autofill > 0
        HANDLE-AUTOFILL(unmatched, matching, cap)

    return matching, autofill, max-flow
```

### FIND-AUGMENTING-PATH-BFS

```
FIND-AUGMENTING-PATH-BFS(G, s, t)
    // Complexity: O(V + E) for BFS graph traversal
    parent = dict with {s: NIL}
    queue = FIFO-QUEUE([s])
    while queue is not empty and t not in parent
        curr = queue.pop_front()
        for each neighbor in G.neighbors(curr)
            residual = G.capacity(curr, neighbor) - G.flow(curr, neighbor)
            if neighbor not in parent and residual > 0
                parent[neighbor] = curr
                queue.push_back(neighbor)

    if t in parent
        return RECONSTRUCT-PATH(parent, s, t)
    return NIL
```

### HANDLE-AUTOFILL

```
HANDLE-AUTOFILL(unmatched, matching, cap)
    // Complexity: O(|unmatched| * |lanes|) = O(1) for fixed 5 lanes
    lane_counts = count of matched players per lane in matching
    for each player p in unmatched
        open_lane = first lane in {TOP, JUG, MID, ADC, SUP} with lane_counts[lane] < cap
        matching[p.id] = open_lane
        lane_counts[open_lane] = lane_counts[open_lane] + 1
```

> **Edmonds-Karp Network Flow Notes**: Lane capacity `cap = 2` is used for 10-player pool matching, and `cap = 1` for 5-player single-team matching. Because player edge capacities are 1, each augmenting path pushes 1 unit of flow. Primary preference edges are added first to give them priority during BFS traversal.

---

## Stage 3 — Team Balancing _(Zichen & Liuyi)_

```
BALANCE-PARTITION(P)                         // split 10 players into two teams, minimizing MMR gap (free split)
    best-gap   = INF
    best-split = NIL
    anchor = P[1]                            // pin one fixed player to team A to kill the red/blue duplicate
    rest   = P \ {anchor}                    // remaining 9 players
    for each subset S subset-of rest with |S| == 4   // C(9,4) == 126 distinct splits
        A = {anchor} union S
        B = P \ A                            // team B = set complement
        g = GAP(A, B)
        if g < best-gap
            best-gap   = g
            best-split = (A, B)
    return best-split, best-gap
```

> Brute-force enumeration: enumerating all 126 splits yields the optimum by
> construction. Brute force is viable only because the fixed 10-player match is a
> small instance; the general BALANCE-OPT problem is **NP-hard** (a
> classification of the general problem, not a property of this instance).

### 32 Role-Preserving Partitioning Scheme _(Liuyi)_

```
SOLVE-32-LANE-BALANCING(lane_players)        // split 5 lanes (2 players each) into two 5-player teams
    // Complexity: O(2^5) = O(32) = O(1) constant search (general problem is NP-hard via PARTITION)
    best-gap   = INF
    best-split = NIL
    // Enumerate 2^5 = 32 role-preserving splits: for each of 5 lanes, assign 1 player to Red, 1 to Blue
    for each choice in CARTESIAN-PRODUCT([0, 1], repeat = 5)
        A, B = ASSEMBLE-TEAMS(lane_players, choice)
        g = GAP(A, B)                        // gap between team MMR means
        if g < best-gap
            best-gap   = g
            best-split = (A, B)
    return best-split, best-gap
```

> Evaluating all 32 role-preserving splits finds the minimum MMR gap over 5 fixed lanes (general problem is NP-hard by reduction from PARTITION). Enumerating all 32 takes `O(1)` time because the 5-lane instance size is fixed.

---

## Two Orderings

### Lane-first _(Liuyi)_ — match, then balance

```
LANE-FIRST(P)
    // Complexity: O(LANE-MATCH) + O(SOLVE-32) = O(1) overall constant time
    matching, _, flow = LANE-MATCH(P, cap = 2)         // cap = 2: match 10 players into 5 lanes (2 per lane); flow == 10
    lane_players = GROUP-BY-LANE(matching, P)           // map each lane to its 2 assigned players
    (A, B), gap = SOLVE-32-LANE-BALANCING(lane_players) // enumerate 2^5 = 32 role-preserving splits, min MMR gap
    matchA = EXTRACT-TEAM-MATCH(matching, A)           // per-team lane assignment derived from pool matching
    matchB = EXTRACT-TEAM-MATCH(matching, B)
    autofill = 0                                       // lane-first guarantees autofill == 0 by construction
    return (A, matchA), (B, matchB), gap, autofill
```

### Balance-first _(Zichen)_ — balance, then match

```
BALANCE-FIRST(P)
    (A, B), gap = BALANCE-PARTITION(P)                 // free 126-split, minimum gap, ignores lanes
    (matchA, autofillA, _) = LANE-MATCH(A, cap = 1)    // match each team independently at cap = 1
    (matchB, autofillB, _) = LANE-MATCH(B, cap = 1)
    autofill = autofillA + autofillB                   // per-team feasibility not guaranteed => may be > 0
    return (A, matchA), (B, matchB), gap, autofill
```

> The asymmetry is the whole story: lane-first buys autofill = 0 with a larger
> gap; balance-first buys a minimum gap with nonzero autofill.

---

## Helpers

```
GAP(R, B)                                    // reported MMR gap = |mean_R - mean_B|
    return | SUM-MMR(R) / |R|  -  SUM-MMR(B) / |B| |   // sum first, then divide by team size, to avoid float drift

SUM-MMR(team)
    s = 0
    for each player p in team
        s = s + p.mmr
    return s
```

---

## Deliberately excluded from the pseudocode

- defensive deep copy, `codes.models` import path, reading the `matching` dict
  vs. `p.assigned_lane` — **engineering details**.
- synthetic data generation, the gamma preference-concentration sweep, metric
  recording — **experimental harness**, belongs under "how we tested" (paper §3 /
  the talk), not the core algorithm. An appendix can be added if a
  complete-program view is wanted, clearly marked "not core algorithm."
