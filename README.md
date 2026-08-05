# CS 5800 Final Project — MOBA Matchmaking

Modeling MOBA matchmaking: from a static snapshot of the queue, assemble a fair,
role-complete 5v5 match, and compare two stage orderings (**lane-first** vs
**balance-first**) to characterize the tradeoff between fairness (team-strength
balance) and preference (lane satisfaction).

## Thesis
- **Feasibility** (can a role-complete match be formed) is **polynomial**
  (Ch. 26 bipartite matching + Hall's theorem).
- **Optimization** (the most balanced match) is **NP-hard** in general
  (Ch. 34, reduction from PARTITION).
- It is tractable in practice only because a single match fixes a small instance (n = 10).

## Approach — three locked stages (executed in order)
1. **Pooling** — sort by MMR, expand a sliding window, use matching as a feasibility
   oracle to extract an MMR-tight, lane-feasible pool of 10 (Ch. 7 + Ch. 26).
2. **Lane matching** — assign players to 5 lanes (capacity 2 each) via unweighted
   max bipartite matching / max-flow (Ch. 26).
3. **Team balancing** — split the 10 players into two teams minimizing MMR gap;
   balanced partition (NP-complete; brute-forced at n = 10) (Ch. 34).

## Repository layout
- `LOCKED_DECISIONS.md` — single source of truth (scope / decisions / terminology). In case of conflict, this file wins.
- `SOP.md` — how we collaborate (short version).
- `AGENTS.md` — behavior rules for AI agents (auto-loaded by Antigravity).
- `code/` — Python implementation, synthetic data generator, experiments.
- `paper/` — proofs and paper (Markdown / LaTeX).
- `results/` — figures and experiment outputs.

## Team
Zichen · Liuyi

*Course: CS 5800 Algorithms*
