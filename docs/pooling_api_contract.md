# Pooling 模块 API Contract (接口描述)

本文档说明 Stage 1 pooling（候选池抽取）的输入要求、输出格式、可调用接口，
以及对 lane matching 模块的依赖假设。

---

## 1. 定位

Stage 1：从一个 static snapshot（`List[Player]`）中，按 MMR 排序后用**固定 size 的
sliding window** 从低到高滑动，取**第一个 lane-feasible 的窗**作为候选池 pool P。

- 对比实验：window size 恒 = 10（5 lane × 2），锁 MMR 紧凑性。
- `pool_size` 参数化仅为 scalability 实验那条线预留（待定，见项目 TODO）。

---

## 2. 外部输入要求 (Required Inputs)

1. **`players` (`List[Player]`)**：一个 static snapshot 的玩家列表。
   - 不建模 online / dynamic queue（out-of-scope）。
   - 每个 `Player`（见 `models.py`）需含：`id`、`mmr`、`pref_primary`、`pref_secondary`。
   - **本模块只读 `p.mmr`**（用于排序）；不读 preference、不碰 `assigned_lane`。
2. **`pool_size` (`int`, 默认 `10`)**：sliding window 宽度。
   - 对比实验恒传（或默认）`10`；scalability 实验才传其它值。

---

## 3. 输出 (Output)

- **返回类型：`Optional[Pool]`**
  - 命中：返回一个 `Pool` dataclass（`Pool(players=<pool_size 个玩家>)`），
    **不返回裸 `List`**（语义清晰 + 对齐 dataclass 接口风格 + 未来可挂元信息）。
  - 无可行窗：返回 `None`。
- **`None` 是预期结果，不是异常。** 实验会故意喂 preference-concentrated 数据触发它。
- **无 side-effect**：内部用 `sorted()` 排在副本上，不 mutate caller 传入的 `players`。

---

## 4. Feasibility 判据（红线）

- 判一个 window 是否可行，**只认 `get_max_flow_count(window, lane_capacity=2) == pool_size`**
  （等价于 autofill_count == 0）。
- **绝不能**用"是不是人人都有 `assigned_lane`"判——autofill 会给不可行的池也塞满
  lane，造成"可行"假象。
- 取**第一个**可行窗即止，不从大窗挑子集、不找"更优"（MMR 紧凑性由输入排序保证）。

---

## 5. 可用接口 (Functions)

```python
find_pool(players: List[Player], pool_size: int = 10) -> Optional[Pool]
```

主入口。排序 → 定宽滑窗 → 首个可行窗包成 `Pool` 返回；无则 `None`。

---

## 6. 对 lane matching 模块的依赖假设 (Dependencies)

本模块依赖 `lane_matching.get_max_flow_count`，并假设：

1. **无 side-effect**：`get_max_flow_count` 不 mutate 传入的 `Player` 对象
   （现实现内部 `deepcopy` 隔离；若将来改实现破坏此假设，pooling 的滑窗探测会被污染）。
2. **返回值封顶 = `5 × lane_capacity`**：`lane_capacity=2` 时封顶 10，不会 > 10。
3. 判可行只用其返回的 max_flow 数值；不消费其 matching / autofill 结果
   （那些是 Stage 2/3 的主力，pooling 只借 feasibility 那个数字）。

> 若上述任一假设变更，需同步通知 pooling 侧。
