## Max-Flow 建图与设计分析 (Graph Construction & Capacity Choice Analysis)

> **参考来源**：本部分整理自 [docs/lane_matching_draft_Liuyi.md](docs/lane_matching_draft_Liuyi.md) 与 [docs/lane_matching_api_contract.md](docs/lane_matching_api_contract.md)。

### 1. 二分流网络拓扑设计 (Bipartite Network Topology)

构建包含虚拟源点 `s`、玩家节点集 `P`、分路节点集 `L` 以及虚拟汇点 `t` 的定向流网络图 `G = (V, E)`：
- **节点集合**：`V = {s, t} ∪ P ∪ L`，其中玩家集 `P = {p_1, p_2, ..., p_n}`（`n = 5` 或 `10`），分路集 `L = {TOP, JUG, MID, ADC, SUP}`（`|L| = 5`）。
- **三层加边与容量规则**：
  1. **源点到玩家边 `(s, p_i)`**：容量 `c(s, p_i) = 1`。约束每位玩家最多仅能贡献 1 单位流量（即每名玩家至多被分配到一个分路位置）。
  2. **玩家到偏好分路边 `(p_i, lane)`**：容量 `c(p_i, lane) = 1`。仅在 `lane` 属于玩家的 `pref_primary`（主选）或 `pref_secondary`（次选）时建立单向边；非偏好分路不建边。
  3. **分路到汇点边 `(lane, t)`**：容量 `c(lane, t) = lane_capacity`。约束该分路位置允许容纳的最大总人数。

### 2. 容量上限 (Capacity Choice) 的选择依据与定量推导

`lane_capacity` 是连通分路节点 `lane` 与汇点 `t` 的边容量 `c(lane, t)`，在算法设计中区分两个核心场景：

#### Scenario A: `lane_capacity = 1` (单小队对局分配场景)
- **应用阶段**：Stage 3（无论是 `lane-first` 还是 `balance-first` 路线下对 5 人小队进行分路匹配）。
- **推导逻辑**：一支标准 MOBA 5v5 小队必须由 5 个不同位置（TOP, JUG, MID, ADC, SUP 各恰好 1 人）构成。设置 `c(lane, t) = 1` 可强制约束每个位置不可重叠。
- **可行性判定**：当且仅当最大流 `max_flow = 5` 时，表示 5 名玩家均可在其主选/次选偏好内被完美分配到 5 个不同位置，无缺口；若 `max_flow < 5`，则触发 Autofill 对剩余未匹配玩家进行补位。

#### Scenario B: `lane_capacity = 2` (10 人候选池 Pooling 校验场景)
- **应用阶段**：Stage 1（Sliding Window 可行性检验 Oracle）及 Stage 2（`lane-first` 路线对 10 人候选池进行匹配）。
- **推导逻辑**：一个合格的 10 人候选池 `Pool`，若要在后续拆分为红蓝两支 5 人小队且均满足分路完整性，该 10 人池必须满足**每个分路位置恰好有 2 名合格玩家**（红蓝队各 1 人）。设置 `c(lane, t) = 2` 精确拟合了这一双队容量限制。
- **可行性判定**：当且仅当最大流 `max_flow = 10` 时，判定该 10 人池具备 `Role-Feasibility`（角色可行性），可安全交由 Stage 2/3 进行拆分。

### 3. Hall's Marriage Theorem 与 Autofill 缺口映射机制

根据霍尔婚配定理（Hall's Marriage Theorem, CLRS Ch 26）：
- 当且仅当玩家偏好集合构成的二分图满足 Hall 条件时，网络存在完美匹配（Perfect Bipartite Matching），此时 `max_flow = |P|`，`autofill_count = 0`。
- 若玩家偏好过于集中（如多名玩家挤占同一位置），残量网络中无法找到足够增广路径，导致 `max_flow < |P|`。
- **缺口人数映射公式**：
  ```text
  autofill_count = |P| - max_flow
  ```
  算法自动将未获得流量分配的 `unmatched_players` 按顺序填入尚未达到 `lane_capacity` 的空缺分路，实现优雅降级。


### 4. 算法复杂度与工程实现 (Edmonds-Karp Algorithm)

- **算法实现**：使用纯 Python 实现的 Edmonds-Karp 算法（采用 BFS 广度优先搜索寻找残量网络 `G_f` 中的最短增广路径）。
- **时间复杂度**：理论上限为 `O(V * E^2)`。由于在 MOBA 单局场景中，节点数 `V = O(n)`，边数 `E = O(n)`，且 `n` 固定为 5 或 10（极小常数），算法在实际运行中为微秒级（ Effective `O(1)`），具有极高的多项式效率与稳定性。

## 零构建算法的逻辑(超简化版)(口述中文转英文自然表述框架)：

1. Step 1: Initialization & Inputs (Dataclass Design)

> *"First, I initialize the parameters and receive the player list. In the data class (`Player`), each player comes with input attributes—ID, primary preference, and secondary preference, `assigned_lane` (initially `None`) and `is_autofilled` (initially `False`)."*

2. Step 2: Construct the Bipartite Graph (Adjacency Dictionary)

> *"Next, I build a Bipartite Graph using an Adjacency Dictionary. I define a Source `s` connected to all players with capacity 1, and a Target Sink `t` connected to all 5 lanes with capacity `lane_capacity`(1 or 2). Then I loop through each player and add directed edges to their preferred lanes—adding primary first, then secondary. In code, this updates our adjacency dictionary."*

3. Step 3: BFS Augmenting Path Search

> *"Step 3 is the BFS function to find an Augmenting Path. It searches for a path from `s` to `t` where residual capacity is greater than 0."*

4. Step 4: Main Edmonds-Karp Loop & Autofill Calculation

> *"Finally, the main loop calls the BFS function repeatedly to push flow until no more augmenting path exists. After that, we count how many players were successfully matched (`max_flow`), and subtract it from total players (5 or 10) to get the  Autofill gap count"*