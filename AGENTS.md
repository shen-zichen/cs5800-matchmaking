# AGENTS.md

本文件是给 AI agent（AG / Claude / 其它）读的行为规则。

## 事实源（source of truth）
- 本项目唯一事实源是 @LOCKED_DECISIONS.md，一切以它为准；与它冲突时以它为准并指出冲突。
- 不要凭训练知识猜项目决定，先读 @LOCKED_DECISIONS.md。
- 已被批准的项目提案见 [Final_Project_Proposal.md](Final_Project_Proposal_submitted.md).因为是已经提交且被批准的提案,所以后续的安排和设计都尽量不要与之冲突,如果必须冲突的话,也要警告⚠️冲突点.
- [Final project proposal requirement](Final project proposal requirement.md)是老师对本次项目的要求

## Scope 护栏（以下是有意排除的，不要主动建议）
- 不建议 Hungarian / Munkres / min-cost-flow / ILP（weighted 版本，已排除）。
- 不建议 Gale–Shapley / RMP / stable matching（two-sided 版本，已排除）。
- 不建议 online / dynamic queue 或 global batch matching（dynamic 版本，已排除）。
- model 已锁定：unweighted、one-sided、capacity-2 bipartite matching（Ch 26，max-flow，polynomial）。以上排除项只能作为 future work / limitations 出现。

## 术语红线
- NP-completeness 是 problem 的 classification，不是 algorithm。我们跑 brute-force enumeration；problem 的分类才是 NP-complete。
- feasibility ≠ complexity：约束更紧影响解是否存在（Hall's condition），不影响多项式复杂度。
- 执行顺序 sort → match → balance。lane-first 与 balance-first 是两个 condition，不是谁对谁错。
- pool P ≠ match：match 恒 10 人；P 是搜索范围。

## 分工
- 可交给 agent：Python implementation、synthetic data generator、跑实验、plotting、debug、git 杂活、boilerplate。
- 不要让 agent 代写：核心 proof、NP-completeness reduction、thesis 论证。可 review / 反驳，但由人来写。

## Git 纪律
- 小 commit，每次 review diff，绝不 Accept All。
- 不要私自commit.每次commit之前先发消息确认summary和description,批准之后再推进

## 公式与 LaTeX 输出格式限制（防 UI 崩溃刷新/闪现）
- **原因**：有些 IDE 的 Webview 在解析流式未闭合的 `$ ... $` 或 `\( ... \)` 符号时，会触发 DOM 渲染报错导致界面 3~5 秒自动刷新/闪现。
- **规定**：
  - **严禁在普通文本中直接输出单/双美元符号 `$ ... $` 或 `\( ... \)`**。
  - **公式与推导**：统一使用代码块（如 ```text 或 ```latex）或行内代码（如 `2^5 = 32`）包裹。
  - **LaTeX 论文源码与数学公式**：必须完整放在 ```latex 或 ```text 代码块中输出，避免出现在普通 Markdown 流中。

