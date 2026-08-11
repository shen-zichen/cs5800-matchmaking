"""
CS 5800 期末项目：MOBA Matchmaking — Lane Matching 单元测试集

包含：
- 格式化与 Raw Player Dataclass 数据输出
- 统一用例日志打印入口 log_match_and_players (Test 1 ~ Test 11 完全统一)
- 包含各种单队与 5v5 双队 Autofill 场景

测试数据置于：tests/test_data_lane_matching.json
"""

import json
import os
import sys
import copy
try:
    import pytest
except ImportError:
    pytest = None

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codes.models import Lane, Player, Team, Match
from codes.lane_matching import (
    solve_lane_matching,
    get_matching,
    get_autofill_count,
    get_max_flow_count,
    get_matching_and_autofill_count,
    get_matching_and_max_flow_count,
)

# 确定外置 JSON 测试数据路径
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data_lane_matching.json")


def load_raw_test_data() -> dict:
    """加载外置 JSON 测试数据"""
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_players(raw_list: list) -> list:
    """将 JSON 中的原始字典数据转译为 dataclass Player 对象"""
    players = []
    for item in raw_list:
        p_id = item["id"]
        mmr = item["mmr"]
        pref_primary = Lane(item["pref_primary"])
        pref_secondary = Lane(item["pref_secondary"]) if item.get("pref_secondary") else None
        players.append(
            Player(
                id=p_id,
                mmr=mmr,
                pref_primary=pref_primary,
                pref_secondary=pref_secondary,
            )
        )
    return players


def bind_matching_to_players(players: list, matching: dict) -> list:
    """
    根据 matching 字典，将分配到的 assigned_lane 与 is_autofilled 绑定更新到 Player 实例上
    """
    for p in players:
        if p.id in matching:
            lane_str = matching[p.id]
            p.assigned_lane = Lane(lane_str) if isinstance(lane_str, str) else lane_str
            pref_sec_str = p.pref_secondary.value if p.pref_secondary else None
            p.is_autofilled = (
                lane_str != p.pref_primary.value
                and (pref_sec_str is None or lane_str != pref_sec_str)
            )
    return players


def log_match_and_players(
    test_name: str,
    players: list,
    matching: dict = None,
    autofill_count: int = None,
    max_flow: int = None,
    match_obj: Match = None,
    bind_to_players: bool = True,
):
    """
    全用例统一控制台日志输出函数 (Test 1 ~ Test 11 风格 100% 保持一致)
    输出包含：
    1. 📦 Raw Player Dataclass 原始对象 (包含所有属性 id, mmr, pref_primary, pref_secondary, assigned_lane, is_autofilled)
    2. 👥 Player Attribute Detail (格式化标点输出与 ⚠️ Autofilled 提示)
    3. 🎯 Returned matching dict (current_match_data)
    4. 📊 Match Statistics (max_flow, autofill_count)
    5. 🏆 Match / Team 完整组局模型 (若有)
    """
    display_players = copy.deepcopy(players)
    if matching and bind_to_players:
        bind_matching_to_players(display_players, matching)

    print(f"\n==================== 🚀 下面是 {test_name} 的结果 ====================")
    
    # 1. 打印原始 Raw Player Dataclass 对象 (包含 Raw data 实例属性)
    print("📦 [Raw Player Dataclass Objects]:")
    for p in display_players:
        print(f"   Raw Player: {p}")

    # 2. 打印格式化解包后的属性列表
    print("👥 [Players Attribute Detail]:")
    for p in display_players:
        p_id = p.id
        assigned = p.assigned_lane.value if p.assigned_lane else (matching.get(p_id) if matching else None)
        pref_sec = p.pref_secondary.value if p.pref_secondary else None
        is_af = p.is_autofilled
        if is_af is None and assigned:
            is_af = (assigned != p.pref_primary.value and (pref_sec is None or assigned != pref_sec))
        af_tag = " (⚠️ Autofilled)" if is_af else ""
        print(
            f"   • Player(id='{p.id}', mmr={p.mmr}, "
            f"pref_primary='{p.pref_primary.value}', pref_secondary={pref_sec}, "
            f"assigned_lane={assigned}, is_autofilled={is_af}){af_tag}"
        )

    # 3. 打印返回的 matching 字典
    if matching is not None:
        print(f"🎯 [Returned matching dict]:\n   current_match_data = {matching}")

    # 4. 打印统计数值
    if autofill_count is not None or max_flow is not None:
        stats = []
        if max_flow is not None:
            stats.append(f"max_flow={max_flow}")
        if autofill_count is not None:
            stats.append(f"autofill_count={autofill_count}")
        print(f"📊 [Match Statistics]: {', '.join(stats)}")

    # 5. 打印 Match / Team 数据模型结构
    if match_obj is not None:
        print("🏆 [Match Model Attributes]:")
        print(f"   • MMR Gap: {match_obj.mmr_gap}")
        print(f"   • Total Autofill: {match_obj.total_autofill}")
        if hasattr(match_obj, "team_red") and hasattr(match_obj, "team_blue"):
            red = match_obj.team_red
            blue = match_obj.team_blue
            print(f"   🔴 Red Team (Autofill Count = {red.autofill_count}):")
            for lane, player in red.lane_map.items():
                lane_str = lane.value if isinstance(lane, Lane) else str(lane)
                af_str = " (⚠️ Autofilled)" if player.is_autofilled else ""
                print(f"      - {lane_str:<4}: Player '{player.id}' (MMR {player.mmr}) | Primary: {player.pref_primary.value:<3}{af_str}")
            print(f"   🔵 Blue Team (Autofill Count = {blue.autofill_count}):")
            for lane, player in blue.lane_map.items():
                lane_str = lane.value if isinstance(lane, Lane) else str(lane)
                af_str = " (⚠️ Autofilled)" if player.is_autofilled else ""
                print(f"      - {lane_str:<4}: Player '{player.id}' (MMR {player.mmr}) | Primary: {player.pref_primary.value:<3}{af_str}")
    print(f"==================== ✅ {test_name} 通过 ====================\n")


# --- 🧪 Test Cases 1 ~ 11: 统一日志格式与 API 流程 ---

def test_case_1_perfect_5():
    """Test Case 1: 5人队伍完美配对组局"""
    raw_data = load_raw_test_data()["test_case_1_perfect_5"]
    players = parse_players(raw_data)

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=1)
    log_match_and_players("Test Case 1: 5人完美配对组局", players, current_match_data, autofill_count, max_flow)

    assert max_flow == 5
    assert autofill_count == 0
    assert len(current_match_data) == 5


def test_case_2_conflict_5():
    """Test Case 2: 5人队伍位置冲突引发 Autofill 组局"""
    raw_data = load_raw_test_data()["test_case_2_conflict_5"]
    players = parse_players(raw_data)

    current_match_data, autofill_count = get_matching_and_autofill_count(players, lane_capacity=1)
    log_match_and_players("Test Case 2: 5人位置冲突Autofill组局", players, current_match_data, autofill_count, max_flow=4)

    assert autofill_count > 0
    assert len(current_match_data) == 5


def test_case_3_feasible_10():
    """Test Case 3: 10人候选池 Stage 1 可行性检测 (Feasibility Oracle)"""
    raw_data = load_raw_test_data()["test_case_3_feasible_10"]
    players = parse_players(raw_data)

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=2)
    is_feasible = (max_flow == 10)
    log_match_and_players("Test Case 3: 10人Pool可行性检测(cap=2)", players, current_match_data, autofill_count, max_flow)

    assert is_feasible is True


def test_case_4_infeasible_10():
    """Test Case 4: 10人候选池 Stage 1 不可行检测 (Feasibility Oracle)"""
    raw_data = load_raw_test_data()["test_case_4_infeasible_10"]
    players = parse_players(raw_data)

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=2)
    is_feasible = (max_flow == 10)
    log_match_and_players("Test Case 4: 10人Pool不可行检测(cap=2)", players, current_match_data, autofill_count, max_flow)

    assert is_feasible is False


def test_case_5_sliding_window_probing():
    """Test Case 5: Stage 1 滑动窗口探查 API 流程模拟"""
    data = load_raw_test_data()
    window_1 = parse_players(data["test_case_5_window_infeasible"])
    window_2 = parse_players(data["test_case_5_window_feasible"])

    m1, af1, mf1 = solve_lane_matching(window_1, lane_capacity=2)
    log_match_and_players("Test Case 5 (Window 1 - Infeasible)", window_1, m1, af1, mf1)

    m2, af2, mf2 = solve_lane_matching(window_2, lane_capacity=2)
    log_match_and_players("Test Case 5 (Window 2 - Feasible)", window_2, m2, af2, mf2)

    assert mf1 < 10
    assert mf2 == 10


def test_case_6_single_preference():
    """Test Case 6: 仅有主选偏好玩家匹配 API 调用"""
    raw_data = load_raw_test_data()["test_case_6_single_pref"]
    players = parse_players(raw_data)

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=1)
    log_match_and_players("Test Case 6: 单偏好玩家匹配", players, current_match_data, autofill_count, max_flow)

    for p in players:
        assert current_match_data[p.id] == p.pref_primary.value


def test_case_7_primary_preference_tie_break():
    """Test Case 7: Primary 偏好优先分配 API 调用模拟"""
    players = [
        Player(id="P1", mmr=1500, pref_primary=Lane.MID, pref_secondary=Lane.TOP),
        Player(id="P2", mmr=1500, pref_primary=Lane.TOP, pref_secondary=Lane.JUG),
        Player(id="P3", mmr=1500, pref_primary=Lane.JUG, pref_secondary=Lane.ADC),
        Player(id="P4", mmr=1500, pref_primary=Lane.ADC, pref_secondary=Lane.SUP),
        Player(id="P5", mmr=1500, pref_primary=Lane.SUP, pref_secondary=Lane.MID),
    ]

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=1)
    log_match_and_players("Test Case 7: Primary偏好优先Tie-Break", players, current_match_data, autofill_count, max_flow)

    assert current_match_data["P1"] == Lane.MID.value


def test_case_8_side_effect_isolation_and_enum_type():
    """Test Case 8: API 纯查询无副作用与返回值类型校验"""
    raw_data = load_raw_test_data()["test_case_1_perfect_5"]
    players = parse_players(raw_data)

    flow_count = get_max_flow_count(players, lane_capacity=1)
    assert flow_count == 5

    # 验证纯隔离性
    test_players = parse_players(raw_data)
    current_match_data = get_matching(test_players, lane_capacity=1)
    log_match_and_players("Test Case 8: API纯查询无副作用与类型校验", test_players, current_match_data, autofill_count=0, max_flow=5, bind_to_players=False)

    for p in test_players:
        assert p.assigned_lane is None
        assert p.is_autofilled is None
        assert current_match_data[p.id] in [lane.value for lane in Lane]


def test_case_9_match_dataclass():
    """Test Case 9: 5v5 对局数据组装与 Match 数据模型构建"""
    raw_data = load_raw_test_data()["test_case_3_feasible_10"]
    players = parse_players(raw_data)

    red_players = players[:5]
    blue_players = players[5:]

    matching_red, autofill_red = get_matching_and_autofill_count(red_players, lane_capacity=1)
    matching_blue, autofill_blue = get_matching_and_autofill_count(blue_players, lane_capacity=1)

    bind_matching_to_players(red_players, matching_red)
    bind_matching_to_players(blue_players, matching_blue)

    team_red = Team(players=red_players, lane_map={p.assigned_lane: p for p in red_players}, autofill_count=autofill_red)
    team_blue = Team(players=blue_players, lane_map={p.assigned_lane: p for p in blue_players}, autofill_count=autofill_blue)

    match_obj = Match(
        team_red=team_red,
        team_blue=team_blue,
        mmr_gap=0.0,
        total_autofill=autofill_red + autofill_blue
    )

    all_players = red_players + blue_players
    all_matching = {**matching_red, **matching_blue}
    log_match_and_players(
        "Test Case 9: 5v5 Match模型构建",
        all_players,
        all_matching,
        autofill_count=match_obj.total_autofill,
        max_flow=10,
        match_obj=match_obj
    )

    assert match_obj.total_autofill == autofill_red + autofill_blue


def test_case_10_autofill_single_team():
    """Test Case 10: 5人队单队 Autofill 组局"""
    raw_data = load_raw_test_data()["test_case_autofill_5v5_single_team"]
    players = parse_players(raw_data)

    current_match_data, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=1)
    log_match_and_players(
        "Test Case 10: 5人队单队 Autofill 组局",
        players,
        current_match_data,
        autofill_count=autofill_count,
        max_flow=max_flow,
    )

    assert autofill_count == 1
    assert set(current_match_data.values()) == {"TOP", "MID", "JUG", "ADC", "SUP"}


def test_case_11_autofill_dual_team_match():
    """Test Case 11: 5v5 双队均触发 Autofill 对局 (Match)"""
    raw_data = load_raw_test_data()["test_case_autofill_5v5_dual_team_match"]
    red_players = parse_players(raw_data["team_red"])
    blue_players = parse_players(raw_data["team_blue"])

    matching_red, autofill_red = get_matching_and_autofill_count(red_players, lane_capacity=1)
    matching_blue, autofill_blue = get_matching_and_autofill_count(blue_players, lane_capacity=1)

    bind_matching_to_players(red_players, matching_red)
    bind_matching_to_players(blue_players, matching_blue)

    team_red = Team(players=red_players, lane_map={p.assigned_lane: p for p in red_players}, autofill_count=autofill_red)
    team_blue = Team(players=blue_players, lane_map={p.assigned_lane: p for p in blue_players}, autofill_count=autofill_blue)

    match_obj = Match(
        team_red=team_red,
        team_blue=team_blue,
        mmr_gap=0.0,
        total_autofill=autofill_red + autofill_blue
    )

    all_players = red_players + blue_players
    all_matching = {**matching_red, **matching_blue}

    log_match_and_players(
        "Test Case 11: 5v5 双队均触发 Autofill 对局",
        all_players,
        all_matching,
        autofill_count=match_obj.total_autofill,
        max_flow=8,
        match_obj=match_obj
    )

    assert autofill_red == 1
    assert autofill_blue == 1
    assert match_obj.total_autofill == 2


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 开始运行 Lane Matching 全套 11 个单元测试用例 (统一格式与 Raw Dataclass 模式)...")
    print("=" * 60)

    test_functions = [
        ("Test 1: 5人完美配对组局", test_case_1_perfect_5),
        ("Test 2: 5人位置冲突Autofill", test_case_2_conflict_5),
        ("Test 3: 10人Pool可行性检测", test_case_3_feasible_10),
        ("Test 4: 10人Pool不可行检测", test_case_4_infeasible_10),
        ("Test 5: Stage 1 滑动探查", test_case_5_sliding_window_probing),
        ("Test 6: 单偏好玩家匹配", test_case_6_single_preference),
        ("Test 7: Primary偏好优先Tie-Break", test_case_7_primary_preference_tie_break),
        ("Test 8: API纯查询无副作用与校验", test_case_8_side_effect_isolation_and_enum_type),
        ("Test 9: 5v5 Match模型构建", test_case_9_match_dataclass),
        ("Test 10: 5人队单队 Autofill 组局", test_case_10_autofill_single_team),
        ("Test 11: 5v5 双队均触发 Autofill 对局", test_case_11_autofill_dual_team_match),
    ]

    passed_count = 0
    for name, func in test_functions:
        try:
            func()
            print(f"✅ {name}: PASSED")
            passed_count += 1
        except Exception as e:
            import traceback
            print(f"❌ {name}: FAILED -> {e}\n{traceback.format_exc()}")

    print("=" * 60)
    print(f"🎉 测试完成！成功通过: {passed_count}/{len(test_functions)}")
    print("=" * 60)
