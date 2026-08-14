"""
CS 5800 Final Project: MOBA Matchmaking — Lane-First End-to-End Pipeline

This module implements the end-to-end matching workflow for the Role-Preserving Strategy.
It first uses Max-Flow to assign the 10-player Pool to 5 lanes (2 players per lane),
then searches over the 2^5 = 32 role-valid splits for the 5v5 match with the smallest
team MMR gap.
"""

import copy
import itertools
from typing import List, Union, Dict, Tuple
from codes.models import Lane, Player, Pool, Team, Match
from codes.lane_matching import solve_lane_matching


def convert_data_to_players(raw_data: Union[Pool, List[Player], List[dict]]) -> List[Player]:
    """
    Placeholder: data-format adapter.
    Adapts various possible input formats (Pool, List[Player], or a list of dicts from JSON).
    If different formats need to be handled in the future (e.g. the data generator may
    produce a different format), add the corresponding conversion logic here.
    """
    if isinstance(raw_data, Pool):
        return raw_data.players
    if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], Player):
        return raw_data
    if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], dict):
        return [
            Player(
                id=item["id"],
                mmr=item["mmr"],
                pref_primary=Lane(item["pref_primary"]),
                pref_secondary=Lane(item["pref_secondary"]) if item.get("pref_secondary") else None,
            )
            for item in raw_data
        ]
    return raw_data  # fallback


def solve_32_lane_balancing(lane_players: Dict[Lane, List[Player]]) -> Tuple[Team, Team, float]:
    """
    Stage 3 Role-Preserving Balancing:
    Enumerate the 2^5 = 32 red/blue split combinations, compute each team's MMR gap,
    and find the split with the smallest gap.

    Args:
        lane_players: players grouped by lane, with exactly 2 players per lane.

    Returns:
        (best_red_team, best_blue_team, best_gap)
    """
    lanes = [Lane.TOP, Lane.JUG, Lane.MID, Lane.ADC, Lane.SUP]
    best_gap = float("inf")
    best_red_team = None
    best_blue_team = None

    # Enumerate the 2^5 = 32 red/blue assignment combinations
    # Using the Python standard library itertools.product
    for choice in itertools.product([0, 1], repeat=5):
        red_players = []
        blue_players = []
        red_map = {}
        blue_map = {}

        for i, lane in enumerate(lanes):
            p1 = lane_players[lane][0]
            p2 = lane_players[lane][1]

            if choice[i] == 0:
                red_players.append(p1)
                red_map[lane] = p1
                blue_players.append(p2)
                blue_map[lane] = p2
            else:
                red_players.append(p2)
                red_map[lane] = p2
                blue_players.append(p1)
                blue_map[lane] = p1

        # Compute the two teams' MMR gap
        red_sum_mmr = sum(p.mmr for p in red_players)
        blue_sum_mmr = sum(p.mmr for p in blue_players)
        gap = abs(red_sum_mmr - blue_sum_mmr) / 5.0

        if gap < best_gap:
            best_gap = gap
            best_red_team = Team(players=red_players, lane_map=red_map, autofill_count=0)
            best_blue_team = Team(players=blue_players, lane_map=blue_map, autofill_count=0)

    return best_red_team, best_blue_team, best_gap


def run_lane_first(pool_input: Union[Pool, List[Player], List[dict]]) -> Match:
    """
    Lane-First matching pipeline (Role-Preserving mode):
    1. Run capacity=2 solve_lane_matching on the 10-player Pool, 2 players per lane.
    2. Call solve_32_lane_balancing to enumerate the 2^5 = 32 splits and compute each
       team's MMR gap.
    3. Return the Match with the smallest MMR gap and autofill=0.

    Input Example:
        pool_input = [
            {"id": "P01", "mmr": 1500, "pref_primary": "TOP", "pref_secondary": "JUG"},
            ... # 10 Player objects or dicts in total
        ]

    Output Example:
        Match(
            team_red=Team(players=[...], autofill_count=0),
            team_blue=Team(players=[...], autofill_count=0),
            mmr_gap=0.0,
            total_autofill=0
        )
    """
    # Parse/convert the data and deep-copy it to avoid polluting the caller's original Pool instance
    raw_players = convert_data_to_players(pool_input)
    players = copy.deepcopy(raw_players)

    # 1. Run capacity=2 Max-Flow lane matching
    matching, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=2)

    # Defensive check: a 10-player pool passed in from Pooling must have max_flow == 10
    if max_flow < 10:
        raise ValueError(
            f"Defensive assertion triggered: the input pool cannot fill all 5 lanes within "
            f"preferences (max_flow={max_flow} < 10). "
            "Please confirm the input Pool has passed the Stage 1 Pooling feasibility check."
        )

    # Group players by lane (2 players per lane)
    lanes = [Lane.TOP, Lane.JUG, Lane.MID, Lane.ADC, Lane.SUP]
    lane_players: Dict[Lane, List[Player]] = {lane: [] for lane in lanes}

    player_dict = {p.id: p for p in players}

    for p_id, lane_str in matching.items():
        lane_enum = Lane(lane_str)
        p = player_dict[p_id]
        p.assigned_lane = lane_enum
        p.is_autofilled = False
        lane_players[lane_enum].append(p)

    # 2. Call the 32-split red/blue subroutine to solve for the best balance
    best_red_team, best_blue_team, best_gap = solve_32_lane_balancing(lane_players)

    # 3. Return the Match object
    return Match(
        team_red=best_red_team,
        team_blue=best_blue_team,
        mmr_gap=best_gap,
        total_autofill=0,
    )