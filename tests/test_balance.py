"""
Stage 3 team balancing tests.

balance_partition is pure MMR with zero dependencies (it never touches lane
matching), so every test is an ORACLE test: hand-built MMR inputs whose correct
answer we can compute by hand. No stubs / monkeypatch needed.

balance_partition(pool) contract:
- input is always a 10-player Pool (upstream find_pool guarantees this)
- output is (team_a, team_b, avg_gap): two teams of 5 + the average MMR gap
- reads only p.mmr; never touches assigned_lane / is_autofilled
"""
import os
import sys

# Same convention as test_lane_matching.py / test_pooling.py:
# put the project root on sys.path and import with the codes. prefix.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from codes.models import Player, Pool, Lane
from codes.balance import balance_partition


def make_pool(mmrs: list) -> Pool:
    """Build a Pool from a list of MMRs. Prefs are dummies (balance ignores lanes)."""
    players = [
        Player(id=f"P{i}", mmr=m, pref_primary=Lane.TOP, pref_secondary=Lane.JUG)
        for i, m in enumerate(mmrs)
    ]
    return Pool(players=players)


# ---------- oracle tests: answer computed by hand ----------

def test_all_equal_gap_is_zero():
    """All MMRs equal -> any split gives equal team sums -> gap is always 0."""
    pool = make_pool([100] * 10)
    team_a, team_b, gap = balance_partition(pool)
    assert gap == 0.0


def test_perfectly_splittable_gap_is_zero():
    """
    Every value appears in a pair [10,10,20,20,30,30,40,40,50,50]:
    a split that separates each pair gives both team sums = 150 -> min gap = 0.
    """
    pool = make_pool([10, 10, 20, 20, 30, 30, 40, 40, 50, 50])
    team_a, team_b, gap = balance_partition(pool)
    assert gap == 0.0


def test_consecutive_1_to_10_min_gap():
    """
    [1..10] sums to 55 (odd) -> the smallest possible team-sum difference is 1,
    never 0. e.g. {1,4,6,7,9}=27 vs {2,3,5,8,10}=28 -> sum gap = 1.
    avg gap = 1 / 5 = 0.2.
    """
    pool = make_pool([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    team_a, team_b, gap = balance_partition(pool)
    assert gap == pytest.approx(0.2)


def test_returns_two_teams_of_five():
    """Structure: exactly 5 players per team."""
    pool = make_pool([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    team_a, team_b, gap = balance_partition(pool)
    assert len(team_a) == 5
    assert len(team_b) == 5


def test_partition_is_complete_and_disjoint():
    """The two teams together = the original 10 players, no overlap, no loss."""
    pool = make_pool([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    team_a, team_b, gap = balance_partition(pool)
    ids_a = {p.id for p in team_a}
    ids_b = {p.id for p in team_b}
    assert ids_a & ids_b == set()                          # disjoint
    assert ids_a | ids_b == {p.id for p in pool.players}   # complete


def test_gap_is_nonnegative():
    """gap is an absolute value scaled by a constant -> always >= 0."""
    pool = make_pool([1, 50, 3, 800, 42, 7, 999, 15, 300, 6])
    team_a, team_b, gap = balance_partition(pool)
    assert gap >= 0.0


def test_returned_gap_matches_teams():
    """
    The returned gap must equal the average difference recomputed from the
    returned teams -- guards against best_gap and best_a/best_b getting out of
    sync (i.e. reporting one split's gap while returning another split's teams).
    """
    pool = make_pool([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    team_a, team_b, gap = balance_partition(pool)
    sum_a = sum(p.mmr for p in team_a)
    sum_b = sum(p.mmr for p in team_b)
    recomputed = abs(sum_a - sum_b) / 5
    assert gap == pytest.approx(recomputed)


def test_does_not_mutate_players():
    """balance reads only mmr; it must not set assigned_lane / is_autofilled."""
    pool = make_pool([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    balance_partition(pool)
    for p in pool.players:
        assert p.assigned_lane is None
        assert p.is_autofilled is None


# ---------- contract test: a non-10 pool must trip the assert ----------

def test_rejects_non_ten_pool():
    """Input is not 10 players -> contract violated -> assert fires."""
    pool = make_pool([100, 200, 300, 400, 500])  # only 5 players
    with pytest.raises(AssertionError):
        balance_partition(pool)


if __name__ == "__main__":
    tests = [
        ("all_equal -> gap 0", test_all_equal_gap_is_zero),
        ("perfectly splittable -> gap 0", test_perfectly_splittable_gap_is_zero),
        ("[1..10] -> gap 0.2", test_consecutive_1_to_10_min_gap),
        ("two teams of 5", test_returns_two_teams_of_five),
        ("complete & disjoint", test_partition_is_complete_and_disjoint),
        ("gap >= 0", test_gap_is_nonnegative),
        ("returned gap matches teams", test_returned_gap_matches_teams),
        ("no mutation", test_does_not_mutate_players),
        ("rejects non-10 pool", test_rejects_non_ten_pool),
    ]
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
            passed += 1
        except Exception as e:
            import traceback
            print(f"FAIL  {name} -> {e}\n{traceback.format_exc()}")
    print(f"\n{passed}/{len(tests)} passed")