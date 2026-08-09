# Lane Matching 模块 API Contract (接口描述)

本文档说明分路匹配算法（Lane Matching）设计的前置输入要求、输出格式以及可调用的接口列表。

---

## 1. 外部输入要求 (Required Inputs)

在调用匹配算法之前，外部必须准备好以下输入数据：

1. **`players` (`List[Player]`)**：玩家列表（5 人队伍或 10 人候选池）。
   - 每个 `Player` 对象（对应 `code/models.py`）必须包含：
     - `id` (`str`): 玩家唯一标识符；
     - `mmr` (`int`): 战力积分；
     - `pref_primary` (`Lane`): 主选分路枚举（如 `Lane.TOP`）；
     - `pref_secondary` (`Optional[Lane]`): 次选分路枚举（可选，如 `Lane.JUG`）。
2. **`lane_capacity` (`int`)**：每条分路的容纳人数上限（默认值为 `1`）。
   - `1`：用于 5 人小队分派分路（TOP, JUG, MID, ADC, SUP 各 1 人）；
   - `2`：用于 10 人候选池分路匹配（TOP, JUG, MID, ADC, SUP 各 2 人）。

---

## 2. 算法输出与内存机制说明 (Outputs & Memory Mechanism)

算法运行完成后，会返回以下 3 项数据：

- **`matching` (`Dict[str, str]`)**：匹配字典 `{player_id: assigned_lane_name}`（例如 `{"P1": "TOP", "P2": "MID", ...}`）；
- **`autofill_count` (`int`)**：被补位的人数缺口（主/次偏好均未拿到的玩家数量）；
- **`max_flow` (`int`)**：成功匹配到主/次偏好分路的总人数（`max_flow = len(players) - autofill_count`）。

### 💡 内存机制说明 (In-Place Mutation)
算法是**直接在内存中“原地更新 (In-Place)”** 传入的原本 `Player` 实例对象，**不会创建新的 `Player` 组**：
- `p.assigned_lane` 被直接更新为分配的 `Lane` 枚举对象；
- `p.is_autofilled` 被直接更新为 `True`（补位）或 `False`（满足偏好）。

> **好处**：后续模块（如 Stage 3 组建 `Team`）持有的依然是同一个 `Player` 对象引用，无需手动重新同步数据。

---

## 3. 可用接口清单 (Functions)

### 主算法入口
```python
solve_lane_matching(players: List[Player], lane_capacity: int = 1) -> (matching, autofill_count, max_flow)
```
运行完整的 Max-Flow 匹配算法与 Autofill 补位，统一返回 `(matching, autofill_count, max_flow)` 三元组。

### 快捷 Getter 接口
如果调用的程序只需要部分字段，可以直接调用以下 Getter 函数：

```python
# 1. 只要匹配结果字典
get_matching(players, lane_capacity=1) -> Dict[str, str]

# 2. 只要补位缺口人数
get_autofill_count(players, lane_capacity=1) -> int

# 3. 只要 Max-Flow 流量数值 (如 Stage 1 Pooling 校验 10 人池可行性)
get_max_flow_count(players, lane_capacity=1) -> int

# 4. 要匹配结果字典 + 补位人数
get_matching_and_autofill_count(players, lane_capacity=1) -> (matching, autofill_count)

# 5. 要匹配结果字典 + Max-Flow 数值
get_matching_and_max_flow_count(players, lane_capacity=1) -> (matching, max_flow_count)
```
