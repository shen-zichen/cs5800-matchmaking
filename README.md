# CS 5800 Final Project — MOBA Matchmaking

Modeling MOBA matchmaking: from a static snapshot of the queue, assemble a fair,
role-complete 5v5 match, and compare two stage orderings (**lane-first** vs
**balance-first**) to characterize the tradeoff between fairness (team-strength
balance) and preference (lane satisfaction).

The two orderings are inspired by two real games: lane-first resembles _Honor of
Kings_ (fill roles first), balance-first resembles _League of Legends_ (balance
strength first). Together they bracket the two ends of the fairness-vs-preference
tradeoff.

## Thesis

- **Feasibility** (can a role-complete match be formed) is **polynomial**
  — Ch. 26 bipartite matching + Hall's theorem.
- **Optimization** (finding the _most balanced_ match) is **NP-hard** in general
  — Ch. 34, reduction from PARTITION.
- It is tractable in practice only because a single match fixes a small instance
  (n = 10), which we solve by brute-force enumeration. The small size does **not**
  change the problem's classification.

## Pipeline — three stages

1. **Pooling** (Stage 1) — sort players by MMR, slide a fixed size-10 window from
   low to high, and use max-flow matching as a feasibility oracle to take the first
   MMR-tight, lane-feasible pool of 10. (Ch. 7 + Ch. 26)
2. **Lane matching** (Stage 2) — assign players to 5 lanes (capacity 2 each) via
   unweighted max bipartite matching / max-flow. (Ch. 26)
3. **Team balancing** (Stage 3) — split the 10 players into two teams minimizing the
   MMR gap; balanced partition, NP-complete in general and brute-forced at n = 10.
   (Ch. 34)

The **lane-first** and **balance-first** orderings run these stages in different
sequences; the comparison experiment feeds the same pool to both and measures the
resulting MMR gap and autofill count.

## Where to find things

**The write-up (`paper/`)**

- [`paper/analysis_report.md`](paper/analysis_report.md) — the main analysis /
  report: problem, model, the NP-hardness reduction, experiments, and results.
- [`paper/pipeline_pseudocode.md`](paper/pipeline_pseudocode.md) — CLRS-style
  pseudocode for the full pipeline.

**The code (`codes/`)** — Python implementation

- `models.py` — core data structures (`Lane`, `Player`, `Pool`, `Team`, `Match`).
- `pooling.py` — Stage 1 pooling (sliding-window feasibility search).
- `lane_matching.py` — Stage 2 max-flow lane matching engine (Edmonds-Karp).
- `balance.py` — Stage 3 team balancing (balanced partition).
- `lane_first_pipeline.py` / `balance_first_pipeline.py` — the two end-to-end orderings.
- `data_generator.py` — synthetic snapshot generator (with a preference-diversity knob).
- `comparison_experiment.py` — runs both orderings over many snapshots.
- `scalability_test.py` — matching scalability experiment.
- `plots.py` — figure generation.

**Results (`results/`)**

- `comparison.csv` — comparison-experiment data.
- `scalability.md` — scalability results.
- `figures/` — generated figures.

**Other**

- `tests/` — pytest test suite.
- `docs/` — design drafts and API-contract archive (development history).

## Running

```bash
# from the repository root
pytest                              # run the test suite
python -m codes.comparison_experiment   # run the lane-first vs balance-first comparison
python -m codes.scalability_test        # run the matching scalability experiment
python -m codes.plots                   # regenerate figures
```

## Team

Zichen Shen · Liuyi Yang

_Course: CS 5800 Algorithms_
