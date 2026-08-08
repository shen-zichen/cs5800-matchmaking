# MOBA Matchmaking 数据模型设计文档 (code/models.py)

本文档对 `code/models.py` 中定义的数据模型字段与用途进行简单说明。

---

## 数据模型说明

### 1. `Lane` (Enum)
定义 MOBA 游戏的 5 个标准分路位置：
- `TOP`：上单
- `JUG`：打野 (Jungle)
- `MID`：中单
- `ADC`：下路 / 射手
- `SUP`：辅助 (Support)

---

### 2. `Player` (dataclass)
代表队列中的单个玩家对象。

| 字段名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `id` | `str` | - | 玩家唯一标识 |
| `mmr` | `int` | - | 隐藏战力积分 (整数) |
| `pref_primary` | `Lane` | - | 主选分路 |
| `pref_secondary` | `Optional[Lane]` | `None` | 次选分路 (可选) |
| `assigned_lane` | `Optional[Lane]` | `None` | 匹配算法分派的分路 (初始未分派) |
| `is_autofilled` | `Optional[bool]` | `None` | 补位状态 (`None`: 未判断; `True`: 补位; `False`: 满足主/次选) |

---

### 3. `Pool` (dataclass)
代表 Stage 1 抽取出的 10 人候选池。

| 字段名 | 类型 | 说明 |
|---|---|---|
| `players` | `List[Player]` | 候选池中的 10 名玩家 |

---

### 4. `Team` (dataclass)
代表由 5 名玩家组成的队伍（红队或蓝队）。

| 字段名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `players` | `List[Player]` | - | 队伍中的 5 名玩家 |
| `lane_map` | `Dict[Lane, Player]` | `{}` | 各分路到对应玩家的映射 |
| `autofill_count` | `int` | `0` | 本队补位人数 |

---

### 5. `Match` (dataclass)
代表最终生成的 5v5 对局结果。

| 字段名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `team_red` | `Team` | - | 红队对象 |
| `team_blue` | `Team` | - | 蓝队对象 |
| `mmr_gap` | `float` | `0.0` | 红蓝两队平均 MMR 差值 |
| `total_autofill` | `int` | `0` | 对局视角下的总补位人数 |

---

## 关联文件
- [models.py](models.py)

