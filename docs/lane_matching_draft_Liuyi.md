# Lane Matching 算法设计稿草稿

本文件用于存放纯 Python 从零实现 Max-Flow 分路匹配算法的代码设计草稿与逻辑说明。

我还没有写完 Python 文件, 现在先上传这个设计文件,以供组内协同进行参考。我之后Lane Matching的.py文件们的代码部分基本上是会和这个一样的。


> 队友对接快速指引：
> 1. **Stage 1 (候选池抽取与可行性校验)**：
>    调用 `get_max_flow_count(players_10, lane_capacity=2)`，只需校验返回的流量数值是否等于 `10`。等于 `10` 即代表该 10 人池满足角色可行性 (Role-Feasible)。
> 2. **Stage 2/3 (5 人小队分派分路与对局组建)**：
>    调用 `solve_lane_matching(players_5, lane_capacity=1)`，返回 `(matching, autofill_count, max_flow)`。算法会**原地更新**传入 `Player` 对象的 `p.assigned_lane` 与 `p.is_autofilled` 字段。


---

## 1. 顺藤摸瓜重构路径函数 `reconstruct_path`

从汇点 `t` 沿着 `parent` 字典倒推回源点 `s`，并反转列表得到从起点到终点的增广路径。

```python
def reconstruct_path(parent, s, t):
    """
    从汇点 t 沿着 parent 字典倒推回源点 s
    返回重构后的路径列表，例如 ['s', 'P1', 'TOP', 't']
    """
    path = []
    curr = t
    
    # 只要当前节点不是 None，就一直往上找父节点
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)  # 拿到当前节点的父节点
        
    # Python 列表自带 reverse() 方法，反转列表变成从 s 到 t
    path.reverse()
    return path
```

---

## 2. 计算瓶颈容量并更新流量函数 `update_flow_along_path`

第一步计算整条路径上的瓶颈容量 `bottleneck`，第二步沿路径更新每条边的三元组状态（流量与退水容量）。
> **经典算法与二分匹配说明**：保留经典 Edmonds-Karp 的最小值求解逻辑，在无权二分匹配及 MOBA 玩家分路匹配设定中，由于每位玩家到源点 s 的容量上限为 1，任意有效增广路径的瓶颈容量 `bottleneck` 均精确等于 `1`。

```python
def update_flow_along_path(path, graph):
    """
    第一步：算出整条路径上的瓶颈容量 (bottleneck)
    第二步：沿路径更新每条边的三元组（流量与退水容量）
    返回：本次增加的流量值 (在二分匹配中精确等于 1)
    """
    # 1. 遍历路径上每对相邻节点 (u, v)，找出最小的剩余残量 (bottleneck)
    bottleneck = float('inf')
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
        
    return bottleneck  # 在二分匹配网络中，返回值精确等于 1
```

---

## 3. 图数据结构 `MatchingGraph`

采用极简双层字典 `edge_dict[u][v] = [cap, flow, is_original]`（边字典）设计：
- `[0]`：最大容量 `cap`
- `[1]`：当前实际流量 `flow`
- `[2]`：是否是原始正向边 `is_original`（`True` 为正向原始边，`False` 为反向退水边）

```python
class MatchingGraph:
    """
    匹配图数据结构（纯 Python 原生字典实现）
    使用 self.edge_dict[u][v] = [cap, flow, is_original] 存储边信息
    """
    def __init__(self):
        self.edge_dict = {}

    def add_node(self, u):
        if u not in self.edge_dict:
            self.edge_dict[u] = {}

    def add_edge(self, u, v, cap):
        """加边：正向原始边标记为 True，反向退水边标记为 False"""
        self.add_node(u)
        self.add_node(v)
        # 正向原始边: [容量 cap, 初始流量 0, 是否原始边 True]
        self.edge_dict[u][v] = [cap, 0, True]
        # 反向退水边: [容量 0, 初始流量 0, 是否原始边 False]
        self.edge_dict[v][u] = [0, 0, False]

    def get_neighbors(self, u):
        """获取节点 u 的所有邻居节点列表"""
        return self.edge_dict.get(u, {}).keys()

    def get_residual_capacity(self, u, v):
        """获取残量容量"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # 原始正向边：剩余容量 = cap - flow
            return cap - flow
        else:
            # 反向退水边：剩余退水容量 = 正向边的实际流量
            return self.edge_dict[v][u][1]

    def augment(self, u, v, bottleneck):
        """沿 (u, v) 灌水/退水更新流量"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # 正向边：流量增加
            self.edge_dict[u][v][1] += bottleneck
        else:
            # 反向边：正向边的流量减少（退水！）
            self.edge_dict[v][u][1] -= bottleneck
```

---

## 4. BFS 寻找增广路 `bfs_find_path`

用 BFS 在残量网络中寻找从 `s` 到 `t` 包含边数最少（最短）的增广路径，返回 `parent` 字典。若残量网络中无增广路，返回 `None`。

```python
from collections import deque

def bfs_find_path(matching_graph, s, t):
    """
    用 BFS 在残量网络中寻找从 s 到 t 包含边数最少的增广路径
    返回 parent 字典；若找不到从 s 到 t 的有效通路，返回 None
    """
    # 记录每个节点的父节点 (带路人)，起点 s 的父节点为 None
    parent = {s: None}
    queue = deque([s])
    
    # 当队列非空且尚未摸到汇点 t 时持续搜图 (无需使用 break)
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
```

---

## 5. 初始化建图函数 `build_matching_graph`

根据输入的玩家列表和分路容量上限，构建包含 `s`、`players`、`lanes` 和 `t` 的匹配流网络图。

```python
# 定义 5 个标准分路统一常量列表
ALL_LANES = ["TOP", "JUG", "MID", "ADC", "SUP"]

def build_matching_graph(players, lane_capacity=1):
    """
    初始化构建二分匹配流网络图 MatchingGraph
    """
    matching_graph = MatchingGraph()
    s = "s"
    t = "t"

    # 1. 连源点 s 到所有玩家 (容量为 1)
    for p in players:
        matching_graph.add_edge(s, p.id, cap=1)

    # 2. 连玩家到偏好分路 (主选与次选容量均为 1)
    for p in players:
        matching_graph.add_edge(p.id, p.pref_primary.value, cap=1)
        matching_graph.add_edge(p.id, p.pref_secondary.value, cap=1)

    # 3. 连 5 个分路到 Sink 't' (容量为 lane_capacity: 5人队为 1，10人池为 2)
    for lane_name in ALL_LANES:
        matching_graph.add_edge(lane_name, t, cap=lane_capacity)

    return matching_graph
```

---

## 6. Edmonds-Karp 主算法 `solve_lane_matching`

求解完整 Max-Flow 分路匹配并提取分配方案、Autofill 补位缺口与 Max-Flow 总数值。

```python
def solve_lane_matching(players, lane_capacity=1):
    """
    纯 Python Max-Flow 分路匹配算法唯一主入口
    
    参数:
        players: 玩家列表 (5人队 或 10人池)
        lane_capacity: 每条分路的容量上限 (5人队为 1，10人池为 2)
    返回:
        (matching, autofill_count, max_flow)
        - matching: 匹配映射字典 {player_id: assigned_lane}
        - autofill_count: 补位人数缺口
        - max_flow: 成功匹配到偏好分路的总人数 (若外部只需流量值，直接取第 3 个返回值)
    """
    # 1. 调用初始化建图函数
    matching_graph = build_matching_graph(players, lane_capacity)
    s = "s"
    t = "t"

    # 2. Edmonds-Karp 主循环：求解 Max-Flow
    max_flow = 0
    parent = bfs_find_path(matching_graph, s, t)
    while parent is not None:
        path = reconstruct_path(parent, s, t)
        update_flow_along_path(path, matching_graph)
        max_flow += 1
        parent = bfs_find_path(matching_graph, s, t)

    # 3. 提取匹配结果
    matching = {}
    lane_counts = {lane_name: 0 for lane_name in ALL_LANES}
    unmatched_players = []

    for p in players:
        # 使用 Python 生成器精确查找该玩家是否有流量为 1 的匹配分路 (无需使用 break)
        matched_lane = next(
            (lane_name for lane_name in ALL_LANES 
             if lane_name in matching_graph.edge_dict.get(p.id, {}) 
             and matching_graph.edge_dict[p.id][lane_name][1] == 1), 
            None
        )
        if matched_lane:
            matching[p.id] = matched_lane
            p.assigned_lane = matched_lane
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
```

---

## 7. Autofill 补位处理函数 `handle_autofill`

未能在偏好分路匹配成功的玩家，自动填入尚未达到容量上限的分路位置。

```python
def handle_autofill(unmatched_players, matching, lane_counts, lane_capacity):
    """
    对未能在偏好分路匹配到的玩家进行 Autofill 补位填空
    """
    for p in unmatched_players:
        # 使用 next() 直接获取第一个尚未达到容量上限的可用分路 (无需使用 break)
        open_lane = next(lane_name for lane_name in ALL_LANES if lane_counts[lane_name] < lane_capacity)
        matching[p.id] = open_lane
        p.assigned_lane = open_lane
        p.is_autofilled = True
        lane_counts[open_lane] += 1
```


---

## 8. 快捷 API 包装函数族 (API Wrapper Functions)

为外部程序、模块或 API 接口调用方提供极度便利的包装函数族。所有包装函数内部均统一调用 `solve_lane_matching` 主算法，无冗余重复代码。

```python
def get_matching(players, lane_capacity=1):
    """
    API 接口：仅获取分路匹配映射字典
    返回: matching (dict) -> {player_id: assigned_lane}
    """
    matching, _, _ = solve_lane_matching(players, lane_capacity)
    return matching


def get_autofill_count(players, lane_capacity=1) -> int:
    """
    API 接口：仅获取补位人数缺口
    返回: autofill_count (int)
    """
    _, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return autofill_count


def get_max_flow_count(players, lane_capacity=1) -> int:
    """
    API 接口：仅获取 Max-Flow 成功匹配偏好的总人数 (用于可行性检查)
    返回: max_flow_count (int)
    """
    _, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return max_flow_count


def get_matching_and_autofill_count(players, lane_capacity=1):
    """
    API 接口组合：获取匹配映射字典与补位缺口人数
    返回: (matching, autofill_count)
    """
    matching, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return matching, autofill_count


def get_matching_and_max_flow_count(players, lane_capacity=1):
    """
    API 接口组合：获取匹配映射字典与 Max-Flow 流量数值
    返回: (matching, max_flow_count)
    """
    matching, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return matching, max_flow_count
```