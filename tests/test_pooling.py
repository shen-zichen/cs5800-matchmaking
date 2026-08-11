"""
Stage 1 pooling 单元测试。
用 stub 替换 Liuyi 的 get_max_flow_count，隔离测试「我们自己的滑窗逻辑」，
不依赖 lane matching 的正确性。
"""
import sys
import os

# 把 codes/ 加进搜索路径，这样 tests/ 里的测试能 import 到 codes/ 里的 pooling、models。
# （和 Liuyi 在 lane_matching.py 里用的 sys.path.insert 是同一招；她 push 后若用了
#   别的方式如 conftest.py，把这两行换成和她一致的即可。）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codes")))

import pytest
from models import Player, Pool, Lane
import pooling


def make_player(pid: str, mmr: int) -> Player:
    """造一个假 player。pref 随便填 —— stub 不真算 matching，所以偏好无所谓。"""
    return Player(id=pid, mmr=mmr, pref_primary=Lane.TOP, pref_secondary=Lane.JUG)


def test_returns_first_feasible_window(monkeypatch):
    """有多个可行窗时，必须返回【第一个】（最低 MMR 那个），不是随便一个。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]

    def fake_max_flow(window, lane_capacity=1):
        return 10 if window[0].mmr == 0 else 0
    monkeypatch.setattr(pooling, "get_max_flow_count", fake_max_flow)

    result = pooling.find_pool(players, pool_size=10)

    assert result is not None
    assert isinstance(result, Pool)
    assert [p.mmr for p in result.players] == list(range(10))


def test_returns_none_when_no_feasible_window(monkeypatch):
    """没有任何可行窗 → 返回 None（预期结果，不是异常）。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(12)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    assert pooling.find_pool(players, pool_size=10) is None


def test_returns_none_when_too_few_players(monkeypatch):
    """人数 < pool_size → 安全返回 None，不报错、不越界。"""
    players = [make_player(f"P{i}", mmr=i) for i in range(8)]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 10)
    assert pooling.find_pool(players, pool_size=10) is None


def test_window_is_sorted_by_mmr(monkeypatch):
    """喂乱序 mmr，find_pool 内部必须先按 mmr 升序排，再滑窗。"""
    players = [make_player(f"P{i}", mmr=m)
               for i, m in enumerate([50, 10, 90, 30, 70, 20, 80, 40, 100, 60, 15, 5])]

    captured = {}
    def fake_max_flow(window, lane_capacity=1):
        if "first_window" not in captured:
            captured["first_window"] = [p.mmr for p in window]
        return 10
    monkeypatch.setattr(pooling, "get_max_flow_count", fake_max_flow)

    pooling.find_pool(players, pool_size=10)

    first = captured["first_window"]
    assert first == sorted(first), "第一个窗不是 mmr 升序 —— 排序没生效"
    assert first == [5, 10, 15, 20, 30, 40, 50, 60, 70, 80]


def test_does_not_mutate_caller_list(monkeypatch):
    """find_pool 不能改到 caller 传进来的原 list 顺序（no side-effect）。"""
    players = [make_player(f"P{i}", mmr=m) for i, m in enumerate([50, 10, 90, 30, 70])]
    original_order = [p.mmr for p in players]
    monkeypatch.setattr(pooling, "get_max_flow_count", lambda w, lane_capacity=1: 0)
    pooling.find_pool(players, pool_size=10)
    assert [p.mmr for p in players] == original_order, "原 list 被 sort 污染了！应该用 sorted() 排副本"