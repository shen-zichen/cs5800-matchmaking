"""
CS 5800 Final Project: MOBA Matchmaking - Balance-First End-to-End Pipeline

Balance-first ("fairness-preserving") strategy: split the 10-player pool into
two teams FIRST (minimizing the MMR gap, ignoring lanes), THEN run lane
matching within each team independently.

Contrast with lane-first (run_lane_first):
- lane-first matches lanes first, so autofill is 0 by construction, but the
  MMR gap is only whatever the 32 role-valid red/blue splits can achieve.
- balance-first fixes the smallest possible MMR gap first, but each team's
  per-team lane feasibility is NOT guaranteed by pool-level feasibility, so
  autofill can be > 0.

The MMR gap here is decided entirely by balance_partition: lane matching only
relabels the already-chosen five players with lanes, it does not change who is
on each team, so the gap is not recomputed. Matching's only new output for
balance-first is the autofill count.
"""

import copy
from typing import Dict
from codes.models import Lane, Player, Pool, Team, Match
from codes.balance import balance_partition
from codes.lane_matching import solve_lane_matching


def _build_team(team_players: list) -> Team:
    """
    Run cap=1 lane matching on one 5-player team, then assemble a Team with its
    lane_map ({Lane: Player}) and autofill_count.

    cap=1: within a single team each of the 5 lanes needs exactly one player.
    """
    # solve_lane_matching deep-copies internally, so the passed-in players are
    # not mutated here; read lane assignments from the returned matching dict.
    matching, autofill_count, _ = solve_lane_matching(team_players, lane_capacity=1)

    # Same group-by pattern as run_lane_first, but cap=1 means one player per
    # lane, so lane_map maps each Lane directly to a single Player (no list).
    player_dict = {p.id: p for p in team_players}
    lane_map: Dict[Lane, Player] = {}
    for p_id, lane_str in matching.items():
        lane_map[Lane(lane_str)] = player_dict[p_id]

    return Team(players=team_players, lane_map=lane_map, autofill_count=autofill_count)


def run_balance_first(pool: Pool) -> Match:
    """
    Balance-first pipeline:
    1. balance_partition(pool) -> two 5-player teams + the minimal MMR gap.
    2. Run cap=1 lane matching within each team (fills lanes, counts autofill).
    3. Assemble a Match. mmr_gap comes straight from step 1 (matching does not
       change team composition), total_autofill is the two teams' autofill sum.
    """
    # Work on a copy so the caller's pool is never mutated -- important because
    # the comparison experiment feeds the SAME pool to both pipelines and must
    # keep it as a clean control between runs.
    pool_copy = Pool(players=copy.deepcopy(pool.players))

    # 1. Split into the minimal-gap 5-5 partition (lanes ignored).
    team_a_players, team_b_players, mmr_gap = balance_partition(pool_copy)

    # 2. Lane-match each team on its own (cap=1).
    team_red = _build_team(team_a_players)
    team_blue = _build_team(team_b_players)

    # 3. Assemble. Gap is reused from step 1; autofill is summed from step 2.
    return Match(
        team_red=team_red,
        team_blue=team_blue,
        mmr_gap=mmr_gap,
        total_autofill=team_red.autofill_count + team_blue.autofill_count,
    )