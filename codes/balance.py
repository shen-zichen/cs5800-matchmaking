"""
CS 5800 Final Project: MOBA Matchmaking - Stage 3 Team Balancing

Splits a lane-feasible 10-player Pool into two teams of five so that the
gap between the two teams' MMR is minimized.

Core algorithm: balanced partition (CLRS Ch. 34). The problem is NP-complete
(reduction from PARTITION); we solve it here by brute-force enumeration, which
is tractable ONLY because a single match is a fixed, tiny instance (n = 10).
Brute-forcing n = 10 does not weaken the NP-complete classification of the
underlying problem (cf. a 4-city TSP being hand-solvable while TSP stays
NP-complete).

De-duplication note: choosing 5 of 10 for team A gives C(10,5) = 252, but
swapping the red/blue labels of a split leaves the MMR gap unchanged, so each
distinct split is counted twice. We pin player 0 to team A and only choose the
other 4 members from the remaining 9, giving C(9,4) = 126 distinct splits with
no double counting.
"""

from typing import List, Tuple
from codes.models import Pool, Player
from itertools import combinations


def balance_partition(pool: Pool) -> Tuple[List[Player], List[Player], float]:
    """
    Find the 5-5 split of a 10-player pool that minimizes the two teams'
    average-MMR gap.

    Only reads Player.mmr. Does NOT touch assigned_lane / is_autofilled, so it
    can serve both orderings (balance-first passes players with no lanes yet;
    lane-first passes already-assigned players and this function ignores that).

    Args:
        pool: a 10-player Pool (guaranteed by the upstream find_pool; the None
            case is handled by the caller, not here).

    Returns:
        (team_a, team_b, avg_gap):
            team_a, team_b: two lists of 5 Player each.
            avg_gap: |sum(team_a.mmr) - sum(team_b.mmr)| / 5, the average
                MMR difference between the two teams.
    """
    # Contract: this function only ever balances one match (5 lanes x 2 = 10).
    # 10 and 5 are MOBA domain constants, not tunable parameters, so a broken
    # length is an upstream bug -> fail fast rather than silently mis-compute.
    n = len(pool.players)
    assert n == 10
    half = n // 2  # players per team; used instead of a bare 5

    # find-min "leaderboard": track the best gap seen so far and the split that
    # produced it. Declared OUTSIDE the loop so they persist across iterations.
    # best_gap starts at +inf so the very first real gap always wins.
    best_gap = float('inf')
    best_a = None
    best_b = None

    # Enumerate the 126 distinct splits: player 0 is pinned to team A, and we
    # choose the other 4 A-members from indices 1..9. combinations yields each
    # 4-tuple of indices lazily, once each, without repetition.
    for combo in combinations(range(1, n), half - 1):
        # Work with indices (plain ints) as player "ID cards": ints go into
        # sets cleanly, so the B team is just the set complement of A.
        a_index = {0} | set(combo)          # A team: pinned 0 + the chosen 4
        b_index = set(range(n)) - a_index   # B team: everyone else

        # Compare with integer sums (avg = sum / half divides by the same
        # constant, so argmin is identical) -> no float, no division in the loop.
        a_sum = sum(pool.players[i].mmr for i in a_index)
        b_sum = sum(pool.players[i].mmr for i in b_index)
        gap = abs(a_sum - b_sum)

        # Strict '<' keeps the first split seen among ties.
        if gap < best_gap:
            best_a = a_index
            best_b = b_index
            best_gap = gap

    # Resolve the winning index sets back into real Player objects.
    a_team = [pool.players[i] for i in best_a]
    b_team = [pool.players[i] for i in best_b]

    # Divide once, at the end, to report the average gap the paper asks for.
    return a_team, b_team, best_gap / half