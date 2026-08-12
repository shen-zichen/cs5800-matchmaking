"""
CS 5800 Final Project: MOBA Matchmaking - Comparison Experiment Runner

Sweeps the preference-diversity knob and, for each setting, feeds the SAME
Stage-1 pool to both orderings (lane-first and balance-first), recording each
one's MMR gap and autofill. This produces the fairness-vs-preference tradeoff
data the paper is built on.

Controlled comparison: both pipelines receive the identical pool per trial, and
that pool is already cap=2 feasible (guaranteed by find_pool). So any autofill
balance-first shows is caused purely by its MMR-first split handing a team a
per-team-infeasible group -- not by a bad pool. (pool-level feasibility does
NOT imply per-team feasibility.)

Output: one CSV row per successful trial, written to results/.
"""

import csv
import os
from dataclasses import dataclass
from typing import List, Optional

from codes.data_generator import generate_snapshot
from codes.pooling import find_pool
from codes.lane_first_pipeline import run_lane_first
from codes.balance_first_pipeline import run_balance_first


@dataclass
class TrialResult:
    """One trial: same pool run through both orderings."""
    concentration: float
    trial: int
    lane_first_gap: float
    lane_first_autofill: int
    balance_first_gap: float
    balance_first_autofill: int


def run_one_trial(concentration: float, trial: int,
                  snapshot_size: int = 50) -> Optional[TrialResult]:
    """
    One trial at a given knob setting:
      1. generate a snapshot (seeded by `trial` for reproducibility),
      2. Stage-1 pool it down to a feasible 10,
      3. run BOTH pipelines on that same pool,
      4. return their gaps + autofills.

    Returns None if no feasible pool exists in the snapshot (a legitimate
    outcome under heavy concentration, not an error) -- the caller skips it.
    """
    snapshot = generate_snapshot(n=snapshot_size, concentration=concentration, seed=trial)

    pool = find_pool(snapshot, pool_size=10)
    if pool is None:
        return None  # no cap=2-feasible window; skip this trial

    lf = run_lane_first(pool)
    bf = run_balance_first(pool)

    return TrialResult(
        concentration=concentration,
        trial=trial,
        lane_first_gap=lf.mmr_gap,
        lane_first_autofill=lf.total_autofill,
        balance_first_gap=bf.mmr_gap,
        balance_first_autofill=bf.total_autofill,
    )


def run_experiment(concentrations: Optional[List[float]] = None,
                   trials_per_setting: int = 100,
                   snapshot_size: int = 50) -> List[TrialResult]:
    """
    Sweep the knob and collect trials.

    Args:
        concentrations: knob values to sweep. Default 0.0..1.0 in steps of 0.1.
        trials_per_setting: independent snapshots per knob value.
        snapshot_size: players per snapshot (the queue Stage 1 pools from).

    Returns:
        a flat list of TrialResult (infeasible trials are dropped).
    """
    if concentrations is None:
        concentrations = [round(0.1 * i, 1) for i in range(11)]  # 0.0..1.0

    results = []
    for conc in concentrations:
        for trial in range(trials_per_setting):
            r = run_one_trial(conc, trial, snapshot_size=snapshot_size)
            if r is not None:
                results.append(r)
    return results


def write_csv(results: List[TrialResult], path: str) -> None:
    """Write results to a CSV Liuyi can read directly for plotting."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "concentration", "trial",
            "lane_first_gap", "lane_first_autofill",
            "balance_first_gap", "balance_first_autofill",
        ])
        for r in results:
            writer.writerow([
                r.concentration, r.trial,
                r.lane_first_gap, r.lane_first_autofill,
                r.balance_first_gap, r.balance_first_autofill,
            ])


def summarize(results: List[TrialResult]) -> dict:
    """
    Aggregate mean gap / autofill per knob value per ordering. Handy for a quick
    console look and as the shape a plot would consume.
    """
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in results:
        buckets[r.concentration].append(r)

    summary = {}
    for conc in sorted(buckets):
        rs = buckets[conc]
        n = len(rs)
        summary[conc] = {
            "n": n,
            "lf_gap": sum(r.lane_first_gap for r in rs) / n,
            "lf_autofill": sum(r.lane_first_autofill for r in rs) / n,
            "bf_gap": sum(r.balance_first_gap for r in rs) / n,
            "bf_autofill": sum(r.balance_first_autofill for r in rs) / n,
        }
    return summary


if __name__ == "__main__":
    results = run_experiment(trials_per_setting=100)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "comparison.csv")
    write_csv(results, out_path)

    summary = summarize(results)
    print(f"{'conc':>5} {'n':>4} | {'LF gap':>8} {'LF af':>6} | {'BF gap':>8} {'BF af':>6}")
    print("-" * 52)
    for conc, s in summary.items():
        print(f"{conc:>5} {s['n']:>4} | {s['lf_gap']:>8.1f} {s['lf_autofill']:>6.2f} "
              f"| {s['bf_gap']:>8.1f} {s['bf_autofill']:>6.2f}")