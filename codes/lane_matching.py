"""
CS 5800 期末项目：MOBA Matchmaking — 分路匹配模块 (Lane Matching Engine)

本模块实现了纯 Python 手写的 Edmonds-Karp Max-Flow 最大流分路匹配算法。
主要包含：
- MatchingGraph: 极简网络流图数据结构
- solve_lane_matching: 求解 5v5 小队或 10 人候选池 Max-Flow 匹配的主入口
- handle_autofill: 对未找到主/次偏好的玩家进行分路补位
- 快捷 API Getter 包装函数族 (get_matching, get_autofill_count, get_max_flow_count 等)

详细说明请参考：docs/lane_matching_api_contract.md 与 docs/lane_matching_draft_Liuyi.md
"""

import copy
import os
import sys
from collections import deque
from typing import List, Dict, Tuple, Optional

# 确保项目根目录在 sys.path 中，支持从任何目录直接执行该脚本
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codes.models import Lane, Player

# 定义 5 个标准分路统一常量列表 (从 Lane 枚举自动派生)
ALL_LANES = [lane.value for lane in Lane]


class MatchingGraph:
    """
    匹配图数据结构（纯 Python 原生字典实现）
    使用 self.edge_dict[u][v] = [cap, flow, is_original] 存储边信息
    """
    def __init__(self):
        self.edge_dict: Dict[str, Dict[str, list]] = {}

    def add_node(self, u: str):
        if u not in self.edge_dict:
            self.edge_dict[u] = {}

    def add_edge(self, u: str, v: str, cap: int):
        """加边：正向原始边标记为 True，反向退水边标记为 False"""
        self.add_node(u)
        self.add_node(v)
        # 正向原始边: [容量 cap, 初始流量 0, 是否原始边 True]
        self.edge_dict[u][v] = [cap, 0, True]
        # 反向退水边: [容量 0, 初始流量 0, 是否原始边 False]
        self.edge_dict[v][u] = [0, 0, False]

    def get_neighbors(self, u: str):
        """获取节点 u 的所有邻居节点列表 (Python 3.7+ 字典保证 key 的插入顺序)"""
        return self.edge_dict.get(u, {}).keys()

    def get_residual_capacity(self, u: str, v: str) -> int:
        """获取残量容量"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # 原始正向边：剩余容量 = cap - flow
            return cap - flow
        else:
            # 反向退水边：剩余退水容量 = 正向边的实际流量
            return self.edge_dict[v][u][1]

    def augment(self, u: str, v: str, bottleneck: int):
        """沿 (u, v) 灌水/退水更新流量"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # 正向边：流量增加
            self.edge_dict[u][v][1] += bottleneck
        else:
            # 反向边：正向边的流量减少（退水！）
            self.edge_dict[v][u][1] -= bottleneck


def reconstruct_path(parent: Dict[str, Optional[str]], s: str, t: str) -> List[str]:
    """
    从汇点 t 沿着 parent 字典倒推回源点 s
    返回重构后的路径列表，例如 ['s', 'P1', 'TOP', 't']
    """
    path = []
    curr: Optional[str] = t
    
    # 只要当前节点不是 None，就一直往上找父节点
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)  # 拿到当前节点的父节点
        
    # Python 列表自带 reverse() 方法，反转列表变成从 s 到 t
    path.reverse()
    return path


def update_flow_along_path(path: List[str], graph: MatchingGraph) -> int:
    """
    第一步：算出整条路径上的瓶颈容量 (bottleneck)
    第二步：沿路径更新每条边的三元组（流量与退水容量）
    返回：本次增加的流量值 (在二分匹配中等于 1)
    """
    # 1. 遍历路径上每对相邻节点 (u, v)，找出最小的剩余残量 (bottleneck)
    bottleneck: int = 999999
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        c_f = graph.get_residual_capacity(u, v)  # 拿到 (u, v) 当前的剩余残量
        bottleneck = min(bottleneck, c_f)
        
    # 2. 拿到瓶颈值后，再次遍历路径，更新每条边的三元组状态
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        graph.augment(u, v, bottleneck)  # 沿 (u, v) 灌水 bottleneck
        
    return bottleneck  # 在二分匹配网络中，返回值等于 1


def bfs_find_path(matching_graph: MatchingGraph, s: str, t: str) -> Optional[Dict[str, Optional[str]]]:
    """
    用 BFS 在残量网络中寻找从 s 到 t 包含边数最少的增广路径
    返回 parent 字典；若找不到从 s 到 t 的有效通路，返回 None
    """
    # 记录每个节点的父节点 (带路人)，起点 s 的父节点为 None
    parent: Dict[str, Optional[str]] = {s: None}
    queue = deque([s])
    
    # 当队列非空且尚未摸到汇点 t 时持续搜图
    while queue and t not in parent:
        curr = queue.popleft()
        
        # 遍历 curr 的所有邻居节点 nxt 
        for nxt in matching_graph.get_neighbors(curr):
            # 校验 1: 残量容量必须大于 0 (可以继续流水或退水)
            # 校验 2: nxt 还没有被访问过 (防止死循环走回头路)
            if nxt not in parent and matching_graph.get_residual_capacity(curr, nxt) > 0:
                parent[nxt] = curr
                queue.append(nxt)
                
    # 检查是否成功找到了到达终点 t 的路径
    if t in parent:
        return parent
    else:
        return None  # 残量网络中不存在从 s 到 t 的增广路了


def build_matching_graph(players: List[Player], lane_capacity: int = 1) -> MatchingGraph:
    """
    初始化构建二分匹配流网络图 MatchingGraph
    """
    matching_graph = MatchingGraph()
    s = "s"
    t = "t"

    # 1. 连源点 s 到所有玩家 (容量为 1)
    for p in players:
        matching_graph.add_edge(s, p.id, cap=1)

    # 2. 连玩家到偏好分路 (主选必有，次选可选；容量均为 1)
    for p in players:
        matching_graph.add_edge(p.id, p.pref_primary.value, cap=1)
        # 防御性校验与日志提示：处理未指定次选分路 (None) 的玩家
        if p.pref_secondary is not None:
            matching_graph.add_edge(p.id, p.pref_secondary.value, cap=1)
        else:
            print(f"[Info] 玩家 {p.id} 未指定次选分路 (pref_secondary is None)，仅连主选分路边。")

    # 3. 连 5 个分路到 Sink 't' (容量为 lane_capacity: 5人队为 1，10人池为 2)
    for lane_name in ALL_LANES:
        matching_graph.add_edge(lane_name, t, cap=lane_capacity)

    return matching_graph


def handle_autofill(unmatched_players: List[Player], matching: Dict[str, str], lane_counts: Dict[str, int], lane_capacity: int):
    """
    对未能在偏好分路匹配到的玩家进行 Autofill 补位填空
    """
    for p in unmatched_players:
        # 防御性保护：当所有分路均达到容量上限时安全返回 None
        open_lane = next((lane_name for lane_name in ALL_LANES if lane_counts[lane_name] < lane_capacity), None)
        if open_lane is None:
            break
        matching[p.id] = open_lane
        p.assigned_lane = Lane(open_lane)  # 统一赋值为 Lane Enum 对象
        p.is_autofilled = True
        lane_counts[open_lane] += 1


def solve_lane_matching(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int, int]:
    """
    纯 Python Max-Flow 分路匹配算法唯一主入口
    
    参数:
        players: 玩家列表 (5人队 或 10人池)
        lane_capacity: 每条分路的容量上限 (5人队为 1，10人池为 2)
    返回:
        (matching, autofill_count, max_flow)
        - matching: 匹配映射字典 {player_id: assigned_lane_name}
        - autofill_count: 补位人数缺口
        - max_flow: 成功匹配到偏好分路的总人数
    """
    # 1. 深拷贝传入的玩家列表，避免修改原始对象
    players_working = copy.deepcopy(players)

    # 2. 调用初始化建图函数
    matching_graph = build_matching_graph(players_working, lane_capacity)
    s = "s"
    t = "t"

    # 3. Edmonds-Karp 主循环：求解 Max-Flow
    max_flow = 0
    parent = bfs_find_path(matching_graph, s, t)
    while parent is not None:
        path = reconstruct_path(parent, s, t)
        update_flow_along_path(path, matching_graph)
        max_flow += 1
        parent = bfs_find_path(matching_graph, s, t)

    # 4. 提取匹配结果
    matching = {}
    lane_counts = {lane_name: 0 for lane_name in ALL_LANES}
    unmatched_players = []

    for p in players_working:
        # 使用 Python 生成器查找该玩家是否有流量为 1 的匹配分路
        matched_lane = next(
            (lane_name for lane_name in ALL_LANES 
             if lane_name in matching_graph.edge_dict.get(p.id, {}) 
             and matching_graph.edge_dict[p.id][lane_name][1] == 1), 
            None
        )
        if matched_lane:
            matching[p.id] = matched_lane
            p.assigned_lane = Lane(matched_lane)  # 统一赋值为 Lane Enum 对象
            p.is_autofilled = False
            lane_counts[matched_lane] += 1
        else:
            unmatched_players.append(p)

    # 4. 如果 max_flow 未能达到总人数 (即存在分路缺口)，触发 Autofill 补位
    expected_flow = len(players)
    if max_flow < expected_flow:
        handle_autofill(unmatched_players, matching, lane_counts, lane_capacity)
        autofill_count = expected_flow - max_flow
    else:
        autofill_count = 0

    # 统一返回三元组
    return matching, autofill_count, max_flow


# --- 快捷 API 包装函数族 (API Wrapper Functions) ---

def get_matching(players: List[Player], lane_capacity: int = 1) -> Dict[str, str]:
    """
    API 接口：仅获取分路匹配映射字典
    返回: matching (dict) -> {player_id: assigned_lane_name}
    """
    matching, _, _ = solve_lane_matching(players, lane_capacity)
    return matching


def get_autofill_count(players: List[Player], lane_capacity: int = 1) -> int:
    """
    API 接口：仅获取补位人数缺口
    返回: autofill_count (int)
    """
    _, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return autofill_count


def get_max_flow_count(players: List[Player], lane_capacity: int = 1) -> int:
    """
    API 接口：仅获取 Max-Flow 成功匹配偏好的总人数 (用于可行性检查)
    返回: max_flow_count (int)
    """
    _, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return max_flow_count


def get_matching_and_autofill_count(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int]:
    """
    API 接口组合：获取匹配映射字典与补位缺口人数
    返回: (matching, autofill_count)
    """
    matching, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return matching, autofill_count


def get_matching_and_max_flow_count(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int]:
    """
    API 接口组合：获取匹配映射字典与 Max-Flow 流量数值
    返回: (matching, max_flow_count)
    """
    matching, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return matching, max_flow_count
