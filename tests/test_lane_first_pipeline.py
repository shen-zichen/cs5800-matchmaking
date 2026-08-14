"""
CS 5800 Final Project: MOBA Matchmaking — Lane-First Pipeline unit test suite

Test data is located at: tests/test_data_lane_matching.json
"""

import json
import os
import sys

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codes.models import Lane, Player, Pool, Match
from codes.lane_first_pipeline import run_lane_first, convert_data_to_players, solve_32_lane_balancing

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data_lane_matching.json")


def load_test_json() -> dict:
    """Load the JSON test data"""
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def print_returned_match_players(match: Match):
    """Print all attributes of the 10 Player objects in the returned Match, one player per line"""
    print("\n==================== 👥 Returned Match Player Objects ====================")
    all_players = match.team_red.players + match.team_blue.players
    for p in all_players:
        sec_val = p.pref_secondary.value if p.pref_secondary else "None"
        assigned_val = p.assigned_lane.value if p.assigned_lane else "None"
        autofill_tag = " (⚠️ Autofilled)" if p.is_autofilled else ""
        print(
            f"Player '{p.id:<4}': MMR={p.mmr} | Primary={p.pref_primary.value:<3} | "
            f"Secondary={sec_val:<3} | Assigned={assigned_val:<3} | Autofilled={p.is_autofilled}{autofill_tag}"
        )


def print_match_summary(match: Match):
    """Structured print of the 5v5 match and the red/blue team lane details"""
    print("\n==================== 🏆 Match Result Overview ====================")
    print(f"📊 Total MMR Gap      : {match.mmr_gap:.2f}")
    print(f"📊 Total Autofill Count: {match.total_autofill}")

    def _print_team(team_name: str, team, emoji: str):
        avg_mmr = sum(p.mmr for p in team.players) / len(team.players)
        print(f"\n{emoji} {team_name} (Avg MMR: {avg_mmr:.1f}, Autofill Count: {team.autofill_count}):")
        lanes_order = [Lane.TOP, Lane.JUG, Lane.MID, Lane.ADC, Lane.SUP]
        for lane in lanes_order:
            player = team.lane_map.get(lane)
            if player:
                autofill_tag = " (⚠️ Autofilled)" if player.is_autofilled else ""
                print(
                    f"   • [{lane.value:<3}] Player '{player.id:<4}' | MMR: {player.mmr} | "
                    f"Primary: {player.pref_primary.value:<3} | Secondary: {player.pref_secondary.value if player.pref_secondary else 'None':<3}{autofill_tag}"
                )

    _print_team("Red Team", match.team_red, "🔴")
    _print_team("Blue Team", match.team_blue, "🔵")
    print("=====================================================================\n")


def test_run_lane_first_with_dict_list():
    """Test running run_lane_first directly with a raw JSON dict list (triggers the Placeholder conversion)"""
    print("\n==================== 🚀 Test 1: run_lane_first with dict list input START ====================")
    data = load_test_json()
    raw_10_feasible = data["test_case_3_feasible_10"]

    # 1. Run the lane-first pipeline
    match_result = run_lane_first(raw_10_feasible)

    # 2. Print all attributes of the returned plain Player objects, one player per line
    print_returned_match_players(match_result)

    # 3. Show the detailed returned Match 5v5 result
    print_match_summary(match_result)

    # 4. Unit test assertions
    assert isinstance(match_result, Match)
    assert match_result.total_autofill == 0
    assert len(match_result.team_red.players) == 5
    assert len(match_result.team_blue.players) == 5

    red_lanes = set(p.assigned_lane for p in match_result.team_red.players)
    blue_lanes = set(p.assigned_lane for p in match_result.team_blue.players)

    assert len(red_lanes) == 5
    assert len(blue_lanes) == 5
    assert match_result.mmr_gap >= 0.0
    print("==================== ✅ Test 1: run_lane_first with dict list input PASSED ====================\n")


def test_run_lane_first_with_pool():
    """Test running run_lane_first with a Pool object"""
    print("==================== 🚀 Test 2: run_lane_first with Pool object input START ====================")
    data = load_test_json()
    players = convert_data_to_players(data["test_case_3_feasible_10"])
    pool = Pool(players=players)

    match_result = run_lane_first(pool)

    # Print the detailed Match statistics
    print(f"📦 Input Pool Size         : {len(pool.players)} players")
    print(f"📊 Returned Match MMR Gap  : {match_result.mmr_gap:.2f}")
    print(f"📊 Total Autofill Count    : {match_result.total_autofill}")
    print(f"🔴 Red Team Players Count  : {len(match_result.team_red.players)}")
    print(f"🔵 Blue Team Players Count : {len(match_result.team_blue.players)}")

    assert isinstance(match_result, Match)
    assert match_result.total_autofill == 0
    assert match_result.team_red.autofill_count == 0
    assert match_result.team_blue.autofill_count == 0
    print("==================== ✅ Test 2: run_lane_first with Pool object input PASSED ====================\n")


def test_does_not_mutate_caller_pool():
    """Test that run_lane_first does not modify the caller's original Pool / Player instances"""
    print("==================== 🚀 Test 3: Anti-Mutation (DeepCopy) Check START ====================")
    data = load_test_json()
    players = convert_data_to_players(data["test_case_3_feasible_10"])
    pool = Pool(players=players)

    print("🔍 Calling run_lane_first(pool)...")
    run_lane_first(pool)

    print("🔍 Verifying original Pool player objects in caller's scope:")
    for p in pool.players:
        print(f"   • Player '{p.id:<4}': assigned_lane={p.assigned_lane} | is_autofilled={p.is_autofilled}")
        assert p.assigned_lane is None
        assert p.is_autofilled is None

    print("✅ Verified 10/10 original players: all assigned_lane == None and is_autofilled == None!")
    print("==================== ✅ Test 3: Anti-Mutation (DeepCopy) Check PASSED ====================\n")


def test_solve_32_lane_balancing_directly():
    """Directly test the extracted 32 red/blue split enumeration algorithm solve_32_lane_balancing"""
    print("==================== 🚀 Test 4: Direct Call to solve_32_lane_balancing START ====================")
    lanes = [Lane.TOP, Lane.JUG, Lane.MID, Lane.ADC, Lane.SUP]
    lane_players = {}
    
    # Build a simple test player set: two players per lane with slightly different MMR
    # TOP: 1000, 1100 -> diff 100
    # JUG: 1000, 1050 -> diff 50
    # MID: 1000, 1000 -> diff 0
    # ADC: 1000, 1000 -> diff 0
    # SUP: 1000, 1000 -> diff 0
    p_id = 1
    for lane in lanes:
        p1 = Player(id=f"P{p_id}", mmr=1000, pref_primary=lane, assigned_lane=lane)
        p_id += 1
        p2_mmr = 1100 if lane == Lane.TOP else (1050 if lane == Lane.JUG else 1000)
        p2 = Player(id=f"P{p_id}", mmr=p2_mmr, pref_primary=lane, assigned_lane=lane)
        p_id += 1
        lane_players[lane] = [p1, p2]

    red, blue, gap = solve_32_lane_balancing(lane_players)
    assert len(red.players) == 5
    assert len(blue.players) == 5
    # The best split should put TOP 1100 and JUG 1000 on one team (SUM=5100), and TOP 1000 and JUG 1050 on the other (SUM=5050), gap = (5100-5050)/5 = 10.0
    assert gap == 10.0
    print(f"📊 Direct solve_32_lane_balancing gap result: {gap}")
    print("==================== ✅ Test 4: Direct Call to solve_32_lane_balancing PASSED ====================\n")


if __name__ == "__main__":
    test_run_lane_first_with_dict_list()
    test_run_lane_first_with_pool()
    test_does_not_mutate_caller_pool()
    test_solve_32_lane_balancing_directly()
    print("==================== 🎉 All Lane-First Pipeline Tests Passed Successfully! ====================")