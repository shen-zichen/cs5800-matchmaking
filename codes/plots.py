"""
CS 5800 Final Project: MOBA Matchmaking - Figure generation.

  Fig 1  tradeoff overview   (comparison.csv)  -- headline: both gaps + BF autofill
  Fig 2  autofill vs knob    (comparison.csv)
  Fig 3  gap spread/variance (comparison.csv)  -- box plot
  Fig 5  matching runtime    (scalability.md)  -- Liuyi's experiment, plotted here

Comparison figures use concentration on the x-axis; scalability uses pool size P
(separate experiments; concentration is irrelevant to the runtime test).

Comparison sweeps concentration 0.0..0.7 only: beyond 0.7 too few snapshots
yield a feasible pool to estimate means reliably. Within 0.0..0.7 the feasible-
pool rate stays ~100%, so a feasibility-rate figure would be a flat line and is
omitted (stated in the paper text instead).
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
FIGDIR = os.path.join(RESULTS, "figures")


def _load_comparison():
    df = pd.read_csv(os.path.join(RESULTS, "comparison.csv"))
    grouped = df.groupby("concentration")
    agg = grouped.agg(
        n=("trial", "count"),
        lf_gap=("lane_first_gap", "mean"),
        bf_gap=("balance_first_gap", "mean"),
        lf_autofill=("lane_first_autofill", "mean"),
        bf_autofill=("balance_first_autofill", "mean"),
    ).reset_index()
    return df, agg


def fig1_tradeoff(agg):
    """Headline: both gap lines (left axis) + balance-first autofill (right)."""
    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.plot(agg["concentration"], agg["lf_gap"], "o-", color="#c0392b",
             label="lane-first  gap")
    ax1.plot(agg["concentration"], agg["bf_gap"], "s-", color="#2980b9",
             label="balance-first  gap")
    ax1.set_xlabel("preference concentration (diversity knob)")
    ax1.set_ylabel("mean MMR gap")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(agg["concentration"], agg["bf_autofill"], "^--", color="#27ae60",
             label="balance-first  autofill")
    ax2.set_ylabel("mean autofill (players)")

    ax1.set_title("Fairness-vs-preference tradeoff\n"
                  "(lane-first autofill = 0 by construction)")

    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lab1 + lab2, loc="upper left", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_tradeoff.png"), dpi=150)
    plt.close(fig)


def fig2_autofill(agg):
    """Balance-first autofill rising with concentration (lane-first flat at 0)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(agg["concentration"], agg["bf_autofill"], "^-", color="#27ae60",
            label="balance-first")
    ax.plot(agg["concentration"], agg["lf_autofill"], "o-", color="#c0392b",
            label="lane-first (= 0)")
    ax.set_xlabel("preference concentration (diversity knob)")
    ax.set_ylabel("mean autofill (players per match)")
    ax.set_title("Autofill cost grows as preferences concentrate")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig2_autofill.png"), dpi=150)
    plt.close(fig)


def fig3_gap_spread(df):
    """Gap distribution per ordering (box plot): lane-first higher AND wider."""
    fig, ax = plt.subplots(figsize=(8, 5))
    data = [df["lane_first_gap"], df["balance_first_gap"]]
    bp = ax.boxplot(data, tick_labels=["lane-first", "balance-first"],
                    showfliers=True, patch_artist=True)
    for patch, color in zip(bp["boxes"], ["#c0392b", "#2980b9"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)
    ax.set_ylabel("MMR gap")
    ax.set_title("Gap distribution: lane-first is higher AND more variable")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig3_gap_spread.png"), dpi=150)
    plt.close(fig)


def _parse_scalability_md(path):
    """Pull (pool_size, time_ms) from Liuyi's scalability.md table rows."""
    sizes, times = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or not cells[0].isdigit():
                continue
            sizes.append(int(cells[0]))
            times.append(float(cells[1].split()[0]))
    return sizes, times


def fig4_scalability():
    """
    Matching runtime vs pool size P (separate experiment; x = pool size).

    The measured curve rises smoothly and near-linearly with P -- i.e. in
    polynomial time. The point is that it does NOT blow up: verifying lane
    feasibility stays in the millisecond range even for thousands of players,
    which is what makes pooling from a large queue tractable. (Contrast the
    balance step, which is NP-hard and would explode -- hence it is confined to
    a fixed 10-player match.)
    """
    path = os.path.join(RESULTS, "scalability.md")
    sizes, times = _parse_scalability_md(path)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, times, "o-", color="#16a085")
    ax.set_xlabel("pool size P (players)")
    ax.set_ylabel("mean matching time (ms)")
    ax.set_title("Matching runtime scales polynomially with pool size")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig4_scalability.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    df, agg = _load_comparison()
    fig1_tradeoff(agg)
    fig2_autofill(agg)
    fig3_gap_spread(df)
    fig4_scalability()
    print(f"Wrote 4 figures to {FIGDIR}")


if __name__ == "__main__":
    main()