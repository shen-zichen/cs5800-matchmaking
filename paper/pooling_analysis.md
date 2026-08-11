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
