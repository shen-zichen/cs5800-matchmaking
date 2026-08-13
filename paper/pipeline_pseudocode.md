# MOBA Matchmaking — Pipeline Pseudocode

> **One program, one pipeline.** The top-level `MATCHMAKING-PIPELINE` calls the
> three stage procedures and the two ordering procedures in turn (like a CLRS
> main procedure calling subroutines). This file states **algorithm logic only**;
> engineering details (defensive copy, import paths, reading the `matching` dict
> vs. `p.assigned_lane`, etc.) are **excluded** — they are not algorithms.
>
> **CLRS edition**: `<!-- TODO: standardize on 3rd ed (§26.3, max-flow in Ch 26) or 4th ed (Ch 24) -->`
> The paper, slides, and both members' pseudocode must agree.
>
> **Ownership**: `POOL` / `BALANCE-PARTITION` / `LANE-FIRST` / `BALANCE-FIRST` by
> Zichen; `LANE-MATCH` (Stage 2) is a placeholder for Liuyi to fill. Match the
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

## Stage 2 — Lane Matching _(Liuyi — placeholder)_

```
LANE-MATCH(P, cap)                           // ── OWNED BY LIUYI: fill in ──
    // INPUT : P   = set of players
    //         cap = lane capacity (1 for a 5-player team; 2 for a 10-player pool)
    // OUTPUT: matching       — each player -> assigned lane
    //         autofill_count — |P| - max_flow (players placed off-preference)
    //         max_flow       — total s->t flow; POOL reads this as the feasibility oracle
    //
    // Method: build the flow network (s->player cap 1; player->preferred lane cap 1;
    //         lane->t cap = cap), run Edmonds-Karp on shortest augmenting paths,
    //         read max_flow, backfill the shortfall as autofill.
    //
    // TERMINOLOGY RED LINE: primary-over-secondary is an emergent effect of BFS
    //         visiting order, NOT a structural guarantee (a reverse-edge undo can
    //         reroute a player from primary to secondary).

    <TODO: Liuyi to fill in>
```

---

## Stage 3 — Team Balancing _(Zichen)_

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

---

## Two Orderings

### Lane-first _(Zichen)_ — match, then balance

```
LANE-FIRST(P)
    (matching, autofill, flow) = LANE-MATCH(P, cap = 2)
    // P was certified pool-feasible in POOL => flow == 10, autofill == 0
    for each lane L in {TOP, JUG, MID, ADC, SUP}
        occupants[L] = { p in P : matching[p] == L }   // exactly 2 players per lane
    best-gap   = INF
    best-split = NIL
    for each of the 2^5 == 32 red/blue choices         // one bit per lane: which occupant goes red
        R = {} ; B = {}
        for each lane L
            (r, b) = split occupants[L] into red/blue by that lane's bit
            R = R union {r} ; B = B union {b}
        g = GAP(R, B)
        if g < best-gap
            best-gap = g ; best-split = (R, B)
    return best-split, best-gap, autofill = 0          // autofill is identically 0 (by construction)
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
