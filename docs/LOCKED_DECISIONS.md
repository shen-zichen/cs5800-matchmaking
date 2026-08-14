# CS 5800 Final Project — Locked Decisions（团队事实基准）

> 本文件是项目的 single source of truth，与已被批准的 [Final_Project_Proposal.md](Final_Project_Proposal_submitted.md) 定稿一致。
> 任何对话若与本文件冲突，以本文件为准。此文件**取代**任何更早的对齐文档（早期文档里的 "sort + bucket"、balance-first 优先顺序等均已作废）。

---

## 0. 一句话定位

建模 MOBA matchmaking：从 queue 的一个 static snapshot 中，组出**一局**（single match）fair、role-complete 的 5v5；并**对比两种阶段顺序**，刻画 fairness（战力平衡）与 preference（分路满足）之间的 tradeoff。

---

## 1. 锁定的三阶段架构（执行顺序 = 编号顺序）

| Stage                        | 内容                                                                                                                                                                   | Algorithm                                                 | CLRS                   | Complexity                |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------------------- | ------------------------- |
| **Stage 1 · Pooling**        | 按 MMR sort，用**固定 size=10 的 sliding window** 从低到高滑动，以 matching 作 feasibility oracle，取**第一个可行窗**作为一个 MMR 紧凑且 lane-feasible 的 10 人 pool P | Quicksort + sliding window（feasibility 检查用 max-flow） | Ch 7（+ Ch 26 判可行） | polynomial                |
| **Stage 2 · Lane Matching**  | 把玩家按 preference 分到 5 条 lane（每 lane capacity 2）                                                                                                               | unweighted max bipartite matching / max-flow（§26.3）     | Ch 26                  | polynomial                |
| **Stage 3 · Team Balancing** | 把 10 人切成两队，使两队 MMR 差最小                                                                                                                                    | balanced partition（NP-complete；n=10 brute-force）       | Ch 34                  | 一般 NP-hard，n=10 可暴力 |

- **MMR** = 玩家隐藏战力值。显示 tier（青铜/白银/…、Iron/Bronze/…）只是 MMR 的粗标签，从 MMR 派生 → 不需要单独 bucketing，只 sort。
- **执行顺序：sort → match/partition → balance**。两种 ordering 的先后不同，见 §2。

### 1.1 Stage 1 窗口策略（固定 10 窗 vs 扩窗）

- **对比实验**：Stage 1 用**固定 size=10 的 sliding window**，从 MMR 排序后的低端向高端滑动；对每个窗调 `get_max_flow_count(window, cap=2) == 10` 判可行，取**第一个可行窗**作为 P（|P| 恒 = 10）。**只滑不挑子集、不扩窗。**
- **为什么固定 10 窗而非从大窗口挑 10 人子集**：max-flow 的可行 10 人组通常**非唯一**，它只吐"某一个"可行解、且按 lane 可行性挑、**完全不看 MMR**。让 max-flow 从大窗口挑 10 人，会把 MMR 紧凑性交给一个不看 MMR 的机制（挑出的人在排序上可能跳着、不紧凑）；要严谨就得在 C(W,10) 个组合里找"满足 max_flow==10 且 MMR 差最小"的那组，时间复杂度爆炸。固定 10 窗把 **MMR 紧凑锁在输入端**（只喂相邻 10 人），max-flow 只负责回答"这 10 人可不可行"。**紧凑是前提，不是事后补救。**
- **feasibility 判据红线**：判可行只认 `max_flow == 10`（等价地 `autofill_count == 0`），**绝不能**用"是不是人人都有 assigned_lane"判——autofill 会给不可行的池也塞满 lane，造成"可行"假象（呼应 §5"matching 不优化 autofill"）。
- **扩窗（让 P 从 10 增大）仅属于 scalability 实验那条线**（见 §3），与对比实验的固定 10 窗互不混用。

---

## 2. 两种 ordering（对比实验的两个 condition）

|                   | 先做                          | 用什么                | 后做                            | autofill                         | 对应游戏          |
| ----------------- | ----------------------------- | --------------------- | ------------------------------- | -------------------------------- | ----------------- |
| **lane-first**    | 按 preference 填满 5 lane × 2 | bipartite matching    | 从 32 种红蓝分法选 MMR gap 最小 | **= 0**（前提：P lane-feasible） | Honor of Kings    |
| **balance-first** | 按 MMR 切两队选 gap 最小      | 枚举 126 种 partition | 每队各跑 matching 分路          | **≥ 0**                          | League of Legends |

- lane-first：**先 match 再 balance**。先按 preference 填满 5 lane × 2，再从 32 种红蓝分法选 MMR gap 最小；因 P 已在 Stage 1 验过 cap=2 可行，切红蓝只是分组、不重分路 → **autofill = 0**，gap 可能偏大。
- balance-first：**先 balance 再 match**。先只按 MMR 枚举 126 种 partition 选 gap 最小，再每队各跑 cap=1 matching 分路；per-team feasibility 不被 pool-level feasibility 保证 → **可能 autofill**，但 gap 最小。
- 两种 ordering **bracket** 了 fairness-vs-preference 的 Pareto frontier 两端。
- tradeoff 出现与否是 **preference diversity** 的函数：偏好越集中 tradeoff 越明显，越分散（趋近全 Fill）越趋同。

---

## 3. 核心 thesis

> **Feasibility**（能否组出 role-complete 一局）是 **polynomial**（Ch 26 matching + Hall's theorem）；
> **Optimization**（最平衡的那一局）在一般情形 **NP-hard**（Ch 34，从 PARTITION 归约）；
> 实际可解，仅因**一局固定 10 人**这个小 instance。

配套实验：

- **对比实验**（P=10，控制变量，同一组 10 人喂两种 ordering；固定 10 窗见 §1.1）→ 展示 tradeoff 结构。数据量靠**大量独立 snapshot**（data generator 调 preference diversity 旋钮）获得，**不从单个 snapshot 榨多局**（后者是 §4 out-of-scope 的 batch matching）。
- **scalability 实验**（P 从 10 增大 / 扩窗）→ 证明 matching 的 polynomiality 在大池选人时是必需的。

---

## 4. Scope

**In-scope（core）**

- 从 static snapshot 组**单局**。
- unweighted、one-sided、capacity-2 bipartite matching；primary preference 仅作 tie-break（当前实现状态见下方注）。
- **所有玩家 primary + secondary 两路均必填**（见下）。
- n=10 brute-force balance。
- 两种 ordering 对比 + matching scalability。

**Out-of-scope（→ future work / limitations）**

- online / dynamic queue（玩家中途 join / cancel、queue-time vs quality tradeoff）。
- 把整个 snapshot 同时切成多局（global batch matching / pool draining）。
- **付费 / 特权单选一条路**（如 Honor of Kings 氪金特权、只选 primary 不选 secondary）：本项目统一规定**所有玩家 primary + secondary 均必填、不建模单选特权**，以统一两款游戏的输入假设、消除 edge case。
- weighted preference（→ assignment problem / Hungarian）。
- two-sided preference + stability（→ RMP / Gale–Shapley）。
- within-team skill variance（只平衡 average）。

> **注（primary 优先的实现状态）**：§4 声称"primary 仅作 tie-break / primary 优先"。当前 lane matching 实现中，primary 与 secondary 两条边容量相等（均为 1），"先满足 primary"是由 BFS 搜索顺序**碰巧**产生的行为，**并非结构性保证**。若 paper 要正式声称 primary 优先，需先确认其被算法保证（例如通过加权 / 分层建图），或在 paper 中如实说明当前为 BFS 顺序副作用。此为待办项，不影响 feasibility 结论。

---

## 5. 术语精度红线

- **NP-completeness 是 classification，不是 algorithm。** 跑的是 **brute-force enumeration**；problem 的分类才是 NP-complete。n=10 能暴力不改变分类（类比：4 城市 TSP 能手算，TSP 仍是 NP-complete）。
- **feasibility ≠ complexity。** 约束更紧 → 影响解是否存在（Hall's condition），**不**影响多项式复杂度。
- **matching 不"优化 autofill"。** 它判定 + 找 perfect matching：能填满 → autofill=0；填不满（Hall 破坏）→ autofill = 缺口数。autofill 是结果的副产品。
- **pool P ≠ match。** match 恒 10 人；P 是 Stage 1 交出的搜索范围（对比实验里钉死 = 10 以控制变量）。
- **pool-level feasibility ≠ per-team feasibility。** Stage 1 保证 10 人整体可填满；balance-first 按 MMR 切出的单队未必可填满 → autofill 从这个缝里来。

---

## 6. 关键数字

- match size：**10**（5 lane × 2）。
- lane-first 的红蓝分法：`2^5 = 32`（role-valid）。
- balance-first 的 partition：**126** distinct splits（`C(10,5)/2`；带红蓝标签是 252）。
- "无 autofill 的干净切法"占比下界 ≈ 12.7%（32/252，worst case，假设玩家锁死单路；实际随 preference diversity 上升）。
- **gap 统一定义**：`mmr_gap = abs(team_a MMR 总和 − team_b MMR 总和) / 每队人数(5)`。两条 pipeline（lane-first / balance-first）**必须用同一口径**，且一律**先减后除**（先做整数减法再除 5），**不可先除后减**——先除后减会引入浮点舍入误差（实测大量 MMR 组合会得到 `0.2000...004` 这类带尾巴的值），破坏两条 pipeline gap 的逐-bit 可比性。

---

## 7. 分工（proposal 版；实际执行互帮互助）

- **Liuyi**：lane matching（Ch 26）+ autofill via Hall's theorem；metric 定义 + plotting。
- **Zichen**：team balancing（Ch 34）+ NP-completeness reduction；pooling（Ch 7）；实验设计 + synthetic data generator + 跑数据 + 写 results。
- **Shared**：两种 ordering 的 integration；testing（含 infeasible-pool edge case）；slide deck；各自录 individual video。
- data-gen 与 results 由同一人（Zichen）把控，因两者调试耦合紧；Zichen 会按需给 Liuyi 分配 sub-task 以保持均衡。

---

## 8. 语言约定

默认中文。专业名词（CS / math / data / 本项目 strategy）以英文为主词，首次括注中文；不把术语翻成中文当主词。

---

## 9. 参考文献

- [Final_Project_Proposal.md](Final_Project_Proposal_submitted.md) (已获批准的项目提案)

---

## 10. 变更记录（Changelog）

- **2026-08-10**：
  - §1 / §1.1：Stage 1 窗口策略明确为**对比实验用固定 size=10 窗、取第一个可行窗**；"扩窗"归入 scalability 实验那条线；补充"为什么固定 10 窗而非挑子集"（max-flow 非唯一解 + 不看 MMR）与 feasibility 判据红线。
  - §1 / §2：修正执行顺序描述——原"先 match 保证每队 role-feasible"仅适用于 lane-first，改为按两种 ordering 分别说明（lane-first 先 match、balance-first 先 partition）。
  - §4：新增"所有玩家 primary + secondary 必填、不建模付费单选特权"为 out-of-scope 约定（统一 HoK / LoL 输入假设）。
  - §4：新增注记——当前"primary 优先"为 BFS 顺序副作用、非结构保证，列为 paper 声称前的待办项。
- **2026-08-11**：
  - §6：新增 **gap 统一定义**（`abs(sum_a − sum_b) / 5`，先减后除），锁死两条 pipeline 的 gap 口径与浮点精度，防止先除后减引入的舍入误差破坏可比性。
