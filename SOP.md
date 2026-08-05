# SOP — 我们怎么协作（简版）

## 一句话
工具各用各的，对齐靠同一个 repo + LOCKED_DECISIONS.md。谁用 AG、谁用别的 AI，都行。

## 1. 单一事实源
LOCKED_DECISIONS.md 是唯一 source of truth（scope / 决定 / 术语）。冲突以它为准。所有 AI 产出都拿它对一遍。

## 2. 工具分工：机器干体力活，人干脑力活
- 交给 AI/agent：Python 实现、synthetic data、跑实验、plotting、debug、git 杂活。
- 人自己做：proof、reduction、thesis 推理、最终验证。LLM 写严格证明常“看着对、其实错一步”，这是拿分的核心，不让 AI 代写。

## 3. 护栏
不采纳 AI 关于 Hungarian / min-cost-flow / ILP / Gale–Shapley 的建议（有意排除）。任何 AI 建议先对照 LOCKED_DECISIONS.md。

## 4. Git 纪律
小 commit、每次 review diff、不 Accept All。各自开 branch，发 PR，另一个人 review 后再 merge。

## 5. 验证 gate
proof 和 reduction 必须另一个人 cross-check 过才算完成。

## 6. 分工（照 proposal §7）
- Liuyi：lane matching（Ch 26）+ autofill via Hall's theorem；metric 定义 + plotting。
- Zichen：team balancing（Ch 34）+ NP reduction；pooling（Ch 7）；实验设计 + data generator + 跑数据 + results。
- 共同：两种 ordering 的 integration；testing（含 infeasible-pool edge case）；slide deck；各自录 video。
- 谁 own 谁写，另一个人 verify。

## 7. 如果用 Antigravity
repo 根目录的 AGENTS.md 会自动加载，已指向 LOCKED_DECISIONS.md + 护栏，不用每次手动喊它读。
