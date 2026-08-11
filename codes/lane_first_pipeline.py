"""
CS 5800 期末项目：MOBA Matchmaking — Lane-First 端到端流水线 (Lane-First Pipeline)

本模块实现角色优先 (Role-Preserving Strategy) 哲学的端到端匹配工作流。
先使用 Max-Flow 将 10 人 Pool 匹配至 5 条分路 (每路 2 人)，
再在 2^5 = 32 种角色合规拆分中寻找两队 MMR Gap 最小的 5v5 对局组合。
"""

import copy
import itertools
from typing import List, Union, Dict
from codes.models import Lane, Player, Pool, Team, Match
from codes.lane_matching import solve_lane_matching


def convert_data_to_players(raw_data: Union[Pool, List[Player], List[dict]]) -> List[Player]:
    """
    Placeholder: 格式转换占位函数。
    用来适配各种可能的数据输入格式 (Pool, List[Player], 或来自 JSON 的 dict 列表)。
    如果未来需要处理不同格式（例如 data generator 可能产出不同格式），在这里补充对应转换逻辑即可。
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


def run_lane_first(pool_input: Union[Pool, List[Player], List[dict]]) -> Match:
    """
    Lane-First 匹配流水线 (Role-Preserving 模式):
    1. 对 10 人 Pool 运行 capacity=2 的 solve_lane_matching，5 条 lane 每路 2 人。
    2. 枚举 2^5 = 32 种角色的红蓝拆分组合，计算两队 MMR Gap。
    3. 返回 MMR Gap 最小且 autofill=0 的 Match 结果。

    示例输入 (Input Example):
        pool_input = [
            {"id": "P01", "mmr": 1500, "pref_primary": "TOP", "pref_secondary": "JUG"},
            ... # 共 10 名 Player 对象或 Dict 列表
        ]

    示例输出 (Output Example):
        Match(
            team_red=Team(players=[...], autofill_count=0),
            team_blue=Team(players=[...], autofill_count=0),
            mmr_gap=0.0,
            total_autofill=0
        )
    """
    # 转译/解析数据并进行深拷贝，防止污染主调方的原始 Pool 实例
    raw_players = convert_data_to_players(pool_input)
    players = copy.deepcopy(raw_players)

    # 1. 跑 capacity=2 的 Max-Flow 分路匹配
    matching, autofill_count, max_flow = solve_lane_matching(players, lane_capacity=2)

    # 防御性校验：按流程从 Pooling 传进来的 10 人池 max_flow 必定等于 10
    if max_flow < 10:
        raise ValueError(
            f"防御性断言触发：传入的候选池无法在偏好内凑满 5 条分路 (max_flow={max_flow} < 10)。"
            "请确认输入 Pool 是否已过 Stage 1 Pooling 的可行性校验。"
        )

    # 按分路归类玩家 (每条分路 2 人)
    lanes = [Lane.TOP, Lane.JUG, Lane.MID, Lane.ADC, Lane.SUP]
    lane_players: Dict[Lane, List[Player]] = {lane: [] for lane in lanes}

    player_dict = {p.id: p for p in players}

    for p_id, lane_str in matching.items():
        lane_enum = Lane(lane_str)
        p = player_dict[p_id]
        p.assigned_lane = lane_enum
        p.is_autofilled = False
        lane_players[lane_enum].append(p)

    best_gap = float("inf")
    best_red_team = None
    best_blue_team = None

    # 2. 枚举 2^5 = 32 种红蓝分配组合
    # 使用 Python 内置标准库 itertools.product
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

        # 计算两队 MMR gap 
        red_sum_mmr = sum(p.mmr for p in red_players)
        blue_sum_mmr = sum(p.mmr for p in blue_players)
        gap = abs(red_sum_mmr - blue_sum_mmr) / 5.0

        if gap < best_gap:
            best_gap = gap
            best_red_team = Team(players=red_players, lane_map=red_map, autofill_count=0)
            best_blue_team = Team(players=blue_players, lane_map=blue_map, autofill_count=0)

    # 3. 返回 Match 对象
    return Match(
        team_red=best_red_team,
        team_blue=best_blue_team,
        mmr_gap=best_gap,
        total_autofill=0,
    )
