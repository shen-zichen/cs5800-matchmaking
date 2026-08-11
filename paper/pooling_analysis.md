## TODOs（pooling）

- [ ] **[cross-file, 待与 Liuyi 确认] `pref_secondary` 收紧为必填**：
      `models.py` 现为 `Optional[Lane] = None`，与 §4"两 pref 必填"不符。
      收紧需同步改 generator 与 matching 的 `is not None` 防御分支。
      不在 pooling 分支内做。pooling 本身不读 secondary，无影响。

- [ ] **[待与 Liuyi 定，跨 scope] scalability 实验做不做 / 怎么做**：
      倾向：可能划为 future work（觉得无聊 + 跨 Liuyi scope，非必做）。
      若做，"P 变大"的 P 指什么：
      (a) snapshot 变大、pool 恒 10 → Liuyi 不动，`pool_size` 可删、只控 len(players)；
      (b) 扩窗、pool 本身变大、match 仍 10 → Liuyi 不动，需 `pool_size`；
      (c) 一局人数变大 → 撞 §5 "match 恒 10" 红线，排除。
      结论：无论 (a)/(b)，Liuyi 核心 max-flow 都不用重写（对人数 agnostic）。

- [ ] **`pool_size` 参数留/删**：绑定上一条。暂**保留**（默认 10，不碍事）；
      删了万一走 (b) 要返工 → "留着不碍事" 比 "删了返工" 安全。

- [ ] **函数动词定名**：`find_pool` / `select_pool` / `search_pool` 待拍。
      倾向 `find`（"可能找不到"合 `Optional[Pool]` + None）。回来定。

- [ ] **[doc 待改，待与 Liuyi 确认] LOCKED_DECISIONS §1 措辞**：
      §1 表格仍写 sliding window"扩窗"，对比实验实际用固定 10 窗
      （§1.1 已澄清、但 §1 表格正文未同步）。确认后统一。

## 2.1 Pooling (Stage 1)

Why do we need pooling at all? A static snapshot may contain hundreds or
thousands of queued players, and balancing teams optimally over a set that
large is computationally intractable — the underlying balancing problem is
NP-complete (see §2.3 Team Balancing). For a snapshot of size 100, choosing
five players for one side already spans $\binom{100}{5} = 75{,}287{,}520$
combinations, far too many to search for a well-balanced match. Pooling
resolves this by first extracting a compact, lane-feasible subset — the
_pool_ $P$ — from the snapshot, reducing the problem to a small instance
($|P| = 10$) that later stages can solve by brute force. We fix $|P| = 10$
because a 5v5 game needs exactly ten players, no more and no fewer.

The choice $|P| = 10$ is deliberate and serves as a controlled variable.
Our comparison experiment feeds the _same_ ten players to both orderings
(lane-first and balance-first); fixing the pool size — together with the
compactness and feasibility requirements below — ensures the two orderings
are compared on one well-formed instance, isolating the ordering itself as
the only variable. We nonetheless parameterize the window size rather than
hard-coding it, so the same procedure extends to a scalability analysis
(§X) in which larger pools probe the matching's polynomial runtime.

The pool $P$ must satisfy two properties. First, its players' MMR must be
compact, so that the eventual teams can be balanced with a small MMR gap; a
random draw of ten players could span wildly different skill levels. Second,
$P$ must be lane-feasible: the ten players must be assignable to the five
lanes (two each) using only their preferred lanes. Note that these two
properties can conflict — the most MMR-compact ten players are not
necessarily lane-feasible — which is precisely why pooling requires a search
rather than a single slice.

### 2.1.1 Method

We first sort the snapshot by MMR, storing the result in a separate list so
the caller's original data is not mutated. We then slide a fixed-width window
of size 10 across the sorted list from lowest to highest MMR, and return the
first lane-feasible window as $P$. Because the list is sorted, any contiguous
window of ten adjacent players is automatically MMR-compact, so window
position alone controls compactness.

### 2.1.2 Feasibility check

We decide whether a window is lane-feasible by reusing the Stage 2 matching
as a feasibility oracle: a window is feasible if and only if its max-flow
value equals $|P| = 10$ (equivalently, its autofill count is zero; see §2.3
Lane Matching). We deliberately do _not_ inspect each player's assigned lane,
because autofill assigns lanes even to infeasible pools, creating a false
appearance of feasibility.

### 2.1.3 Why a fixed window rather than a growing one

One might instead slide a variable-width window and let max-flow pick ten
feasible players from a larger window $W$. We avoid this for two reasons.
First, max-flow only certifies feasibility; among a larger window its ten
chosen players are not unique and are selected without any regard to MMR, so
they may be scattered rather than adjacent — breaking compactness. Second,
recovering the _most_ compact feasible ten from $W$ would require searching
$\binom{|W|}{10}$ subsets, which is combinatorially explosive. A fixed window
keeps MMR-compactness a built-in property of the input rather than something
to be recovered afterward.

### 2.1.4 Complexity

Sorting is $O(n \log n)$, the scan visits $O(n)$ windows, and each
feasibility check is a single polynomial-time max-flow computation. The whole
stage is therefore polynomial — consistent with the "feasibility is
polynomial" half of our thesis (§Thesis).
