"""
Stage 1 pooling 测试。
- 前 5 个：用 stub 隔离测试滑窗逻辑（不依赖 lane matching 正确性）。
- 后 2 个：集成测试，用【真】get_max_flow_count + 队友 JSON 数据，验证端到端挑池。
"""
import json
import os
import sys

# 和队友 test_lane_matching.py 一致：把【项目根】加入 path，用 codes. 前缀 import。
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from codes.models import Player, Pool, Lane
from codes import pooling

# 复用队友的 JSON 测试数据（同一个文件）
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data_lane_matching.json")


def load_data() -> dict:
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_players(raw_list: list) -> list:
    """把 JSON 原始 dict 转成 Player（与队友 parse_players 同逻辑）。"""
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
    """造假 player。stub 测试用，pref 随便填。"""
    return Player(id=pid, mmr=mmr, pref_primary=Lane.TOP, pref_secondary=Lane.JUG)


# ---------- 单元测试：stub 隔离滑窗逻辑 ----------

def test_returns_first_feasible_window(monkeypatch):
    """有多个可行窗时，返回【第一个】（最低 MMR 那个）。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]
    def fake(window, lane_capacity=1):
        return 10 if window[0].mmr == 0 else 0
    monkeypatch.setattr(pooling, "get_max_flow_count", fake)
    result = pooling.find_pool(players, pool_size=10)
    assert result is not None
    assert isinstance(result, Pool)
    assert [p.mmr for p in result.players] == list(range(10))


def test_returns_none_when_no_feasible_window(monkeypatch):
    """没有可行窗 → None。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    assert pooling.find_pool(players, pool_size=10) is None


def test_returns_none_when_too_few_players(monkeypatch):
    """人数 < pool_size → 安全返回 None。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(8)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 10)
    assert pooling.find_pool(players, pool_size=10) is None


def test_window_is_sorted_by_mmr(monkeypatch):
    """乱序输入 → 内部按 mmr 升序。"""
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
    """不污染 caller 原 list 顺序。"""
    players = [make_player(f"P{i}", mmr=m) for i, m in enumerate([50, 10, 90, 30, 70])]
    original = [p.mmr for p in players]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    pooling.find_pool(players, pool_size=10)
    assert [p.mmr for p in players] == original


# ---------- 集成测试：真 get_max_flow_count + 队友 JSON 数据 ----------

def test_integration_feasible_pool_is_found():
    """端到端：喂一组【已知可行】的 10 人，find_pool 用真 matching 应挑出非 None 的 Pool。"""
    players = parse_players(load_data()["test_case_3_feasible_10"])
    result = pooling.find_pool(players, pool_size=10)
    assert result is not None
    assert isinstance(result, Pool)
    assert len(result.players) == 10


def test_integration_infeasible_pool_returns_none():
    """端到端：喂一组【已知不可行】的 10 人，唯一窗不可行 → find_pool 应返回 None。"""
    players = parse_players(load_data()["test_case_4_infeasible_10"])
    result = pooling.find_pool(players, pool_size=10)
    assert result is None