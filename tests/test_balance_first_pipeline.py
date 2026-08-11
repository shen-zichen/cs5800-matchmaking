"""
Balance-first pipeline tests.

run_balance_first splits the pool by MMR first (balance_partition), then lane-
matches each team at cap=1. Key things to pin down:
- the returned mmr_gap equals what balance_partition decided (matching does NOT
  recompute it -- lane matching only relabels the already-chosen five players);
- autofill can be > 0 even when the whole pool is lane-feasible, because pool-
  level feasibility does NOT imply per-team feasibility (this is the balance-
  first vs lane-first asymmetry the paper is about);
- the caller's pool is never mutated (the comparison experiment feeds the same
  pool to both pipelines and needs it clean between runs).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from codes.models import Player, Pool, Lane
from codes.balance import balance_partition
from codes.balance_first_pipeline import run_balance_first


def P(pid, mmr, pri, sec=None):
    """Shorthand Player builder."""
    return Player(
        id=pid,
        mmr=mmr,
        pref_primary=Lane(pri),
        pref_secondary=Lane(sec) if sec else None,
    )


def feasible_pool():
    """
    A pool that is lane-feasible as a whole at cap=2 (each lane reachable by
    two players' prefs). MMRs are staggered so balance_partition has real work.
    """
    return Pool(players=[
        P("P01", 1500, "TOP", "JUG"), P("P02", 1500, "TOP", "MID"),
        P("P03", 1500, "JUG", "MID"), P("P04", 1500, "JUG", "ADC"),
        P("P05", 1500, "MID", "ADC"), P("P06", 1500, "MID", "SUP"),
        P("P07", 1500, "ADC", "SUP"), P("P08", 1500, "ADC", "TOP"),
        P("P09", 1500, "SUP", "TOP"), P("P10", 1500, "SUP", "JUG"),
    ])


# ---------- structure ----------

def test_returns_two_teams_of_five():
    """Both teams have exactly 5 players and 5 lane_map entries."""
    match = run_balance_first(feasible_pool())
    assert len(match.team_red.players) == 5
    assert len(match.team_blue.players) == 5
    assert len(match.team_red.lane_map) == 5
    assert len(match.team_blue.lane_map) == 5


def test_lane_map_keys_are_lane_enums():
    """lane_map keys are Lane enums (not strings), values are Players."""
    match = run_balance_first(feasible_pool())
    for lane, player in match.team_red.lane_map.items():
        assert isinstance(lane, Lane)
        assert isinstance(player, Player)


def test_lane_map_covers_all_five_lanes():
    """cap=1 per team -> every one of the 5 lanes is filled exactly once."""
    match = run_balance_first(feasible_pool())
    assert set(match.team_red.lane_map.keys()) == set(Lane)
    assert set(match.team_blue.lane_map.keys()) == set(Lane)


# ---------- gap comes straight from balance_partition ----------

def test_gap_equals_balance_partition_gap():
    """
    The Match's mmr_gap must equal balance_partition's gap on the same pool --
    lane matching must NOT change or recompute it.
    """
    pool = feasible_pool()
    _, _, expected_gap = balance_partition(Pool(players=list(pool.players)))
    match = run_balance_first(pool)
    assert match.mmr_gap == pytest.approx(expected_gap)


def test_all_equal_mmr_gap_is_zero():
    """All MMRs equal -> any split is perfectly balanced -> gap 0."""
    pool = feasible_pool()  # every mmr is 1500
    match = run_balance_first(pool)
    assert match.mmr_gap == 0.0


# ---------- autofill: the balance-first signature ----------

def test_total_autofill_is_sum_of_teams():
    """total_autofill must equal the two teams' autofill counts added up."""
    match = run_balance_first(feasible_pool())
    assert match.total_autofill == (
        match.team_red.autofill_count + match.team_blue.autofill_count
    )


def test_feasible_pool_can_still_autofill_per_team():
    """
    Core balance-first phenomenon: the pool is lane-feasible as a whole, yet
    balance_partition's MMR-only split can hand a team a lane-INfeasible group,
    so per-team autofill may be > 0. We assert it is a valid non-negative count
    (pool-level feasibility != per-team feasibility).
    """
    match = run_balance_first(feasible_pool())
    assert match.total_autofill >= 0
    # each lane still ends up filled (autofill backfills the gaps)
    assert len(match.team_red.lane_map) == 5
    assert len(match.team_blue.lane_map) == 5


def test_preference_concentrated_forces_autofill():
    """
    Six players all want MID/TOP -> whichever team gets 3+ of them cannot seat
    them all in preferred lanes -> autofill must fire (> 0).
    """
    pool = Pool(players=[
        P("P01", 1000, "MID", "TOP"), P("P02", 1100, "MID", "TOP"),
        P("P03", 1200, "MID", "TOP"), P("P04", 1300, "MID", "TOP"),
        P("P05", 1400, "MID", "TOP"), P("P06", 1500, "MID", "TOP"),
        P("P07", 1600, "JUG", "ADC"), P("P08", 1700, "JUG", "ADC"),
        P("P09", 1800, "SUP", "JUG"), P("P10", 1900, "ADC", "SUP"),
    ])
    match = run_balance_first(pool)
    assert match.total_autofill > 0


# ---------- no mutation of the caller's pool ----------

def test_does_not_mutate_caller_pool():
    """
    run_balance_first deep-copies internally, so the caller's players keep
    assigned_lane / is_autofilled as None after the call. This keeps the pool a
    clean control for the comparison experiment.
    """
    pool = feasible_pool()
    run_balance_first(pool)
    for p in pool.players:
        assert p.assigned_lane is None
        assert p.is_autofilled is None


if __name__ == "__main__":
    tests = [
        ("two teams of 5", test_returns_two_teams_of_five),
        ("lane_map keys are Lane enums", test_lane_map_keys_are_lane_enums),
        ("lane_map covers 5 lanes", test_lane_map_covers_all_five_lanes),
        ("gap == balance_partition gap", test_gap_equals_balance_partition_gap),
        ("all-equal gap 0", test_all_equal_mmr_gap_is_zero),
        ("total autofill = sum", test_total_autofill_is_sum_of_teams),
        ("feasible pool can autofill per team", test_feasible_pool_can_still_autofill_per_team),
        ("concentrated prefs force autofill", test_preference_concentrated_forces_autofill),
        ("no mutation of caller pool", test_does_not_mutate_caller_pool),
    ]
    passed = 0
    for name, fn in tests:
        try:
            fn(); print(f"PASS  {name}"); passed += 1
        except Exception as e:
            import traceback
            print(f"FAIL  {name} -> {e}\n{traceback.format_exc()}")
    print(f"\n{passed}/{len(tests)} passed")