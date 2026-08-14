"""
Stage 1 pooling tests.
- First 5: use stubs to test the sliding-window logic in isolation (independent of lane matching correctness).
- Last 2: integration tests using the REAL get_max_flow_count + teammate's JSON data, verifying end-to-end pool selection.
"""
import json
import os
import sys

# Consistent with teammate's test_lane_matching.py: add the PROJECT ROOT to path, import with the codes. prefix.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from codes.models import Player, Pool, Lane
from codes import pooling

# Reuse the teammate's JSON test data (the same file)
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data_lane_matching.json")


def load_data() -> dict:
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_players(raw_list: list) -> list:
    """Convert raw JSON dicts into Player objects (same logic as the teammate's parse_players)."""
    players = []
    for item in raw_list:
        pref_secondary = Lane(item["pref_secondary"]) if item.get("pref_secondary") else None
        players.append(Player(
            id=item["id"],
            mmr=item["mmr"],
            pref_primary=Lane(item["pref_primary"]),
            pref_secondary=pref_secondary,
        ))
    return players


def make_player(pid: str, mmr: int) -> Player:
    """Build a fake player. For stub tests; pref filled arbitrarily."""
    return Player(id=pid, mmr=mmr, pref_primary=Lane.TOP, pref_secondary=Lane.JUG)


# ---------- Unit tests: stub-isolated sliding-window logic ----------

def test_returns_first_feasible_window(monkeypatch):
    """When there are multiple feasible windows, return the FIRST one (the lowest-MMR one)."""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]
    def fake(window, lane_capacity=1):
        return 10 if window[0].mmr == 0 else 0
    monkeypatch.setattr(pooling, "get_max_flow_count", fake)
    result = pooling.find_pool(players, pool_size=10)
    assert result is not None
    assert isinstance(result, Pool)
    assert [p.mmr for p in result.players] == list(range(10))


def test_returns_none_when_no_feasible_window(monkeypatch):
    """No feasible window -> None."""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    assert pooling.find_pool(players, pool_size=10) is None


def test_returns_none_when_too_few_players(monkeypatch):
    """Player count < pool_size -> safely return None."""
    players = [make_player(f"P{i}", mmr=i) for i in range(8)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 10)
    assert pooling.find_pool(players, pool_size=10) is None


def test_window_is_sorted_by_mmr(monkeypatch):
    """Unsorted input -> internally sorted by mmr ascending."""
    players = [make_player(f"P{i}", mmr=m)
               for i, m in enumerate([50, 10, 90, 30, 70, 20, 80, 40, 100, 60, 15, 5])]
    captured = {}
    def fake(window, lane_capacity=1):
        captured.setdefault("first", [p.mmr for p in window])
        return 10
    monkeypatch.setattr(pooling, "get_max_flow_count", fake)
    pooling.find_pool(players, pool_size=10)
    assert captured["first"] == sorted(captured["first"])
    assert captured["first"] == [5, 10, 15, 20, 30, 40, 50, 60, 70, 80]


def test_does_not_mutate_caller_list(monkeypatch):
    """Do not pollute the caller's original list order."""
    players = [make_player(f"P{i}", mmr=m) for i, m in enumerate([50, 10, 90, 30, 70])]
    original = [p.mmr for p in players]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    pooling.find_pool(players, pool_size=10)
    assert [p.mmr for p in players] == original


# ---------- Integration tests: real get_max_flow_count + teammate's JSON data ----------

def test_integration_feasible_pool_is_found():
    """End-to-end: feed a KNOWN-feasible group of 10; find_pool using real matching should return a non-None Pool."""
    players = parse_players(load_data()["test_case_3_feasible_10"])
    result = pooling.find_pool(players, pool_size=10)
    assert result is not None
    assert isinstance(result, Pool)
    assert len(result.players) == 10


def test_integration_infeasible_pool_returns_none():
    """End-to-end: feed a KNOWN-infeasible group of 10; the only window is infeasible -> find_pool should return None."""
    players = parse_players(load_data()["test_case_4_infeasible_10"])
    result = pooling.find_pool(players, pool_size=10)
    assert result is None