# Standard Pseudocode: Lane-First Matchmaking Pipeline

> 📝 **Liuyi 的 Pseudocode 整理笔记 (Lane-First Pipeline)**：
> 这是我们项目核心的 **Lane-First (角色优先/Role-Preserving) 端到端匹配流水线**。
> 先使用 Capacity=2 的 Max-Flow 算法把 10 人 Pool 填满 5 条分路 (每路 2 人)，
> 再枚举 $2^5 = 32$ 种角色合规拆分组合，寻找两队 MMR Gap 最小的 5v5 最佳对局

```python
def Run_Lane_First_Pipeline(pool):
    """
    INPUT: 
        pool: 10-Player candidate pool P (Feasibility guaranteed in Stage 1)
    OUTPUT: 
        match: Best 5v5 Match (team_red, team_blue, mmr_gap, total_autofill=0)
    """

    # --- Step 1: Stage 2 Lane Matching (cap=2) ---
    # 每条分路匹配 2 名玩家，得到 5 条分路上的玩家归类
    matching, autofill_count, max_flow = Lane_Matching_Max_Flow(pool, lane_capacity=2)
    lane_players = Group_Players_By_Lane(matching, pool)

    # --- Step 2: Stage 3 Role-Preserving Balancing (32 Partitions) ---
    best_gap = infinity
    best_match = None

    # 枚举 2^5 = 32 种角色合规的红蓝对局拆分
    # (对 5 条分路的每一条，各放 1 人去红队，1 人去蓝队)
    for choice in Cartesian_Product([0, 1], repeat=5):
        team_red, team_blue = Assemble_Teams(lane_players, choice)

        # 计算两队的平均 MMR 差距 (先减后除 5)
        mmr_gap = abs(Sum_MMR(team_red) - Sum_MMR(team_blue)) / 5.0

        if mmr_gap < best_gap:
            best_gap = mmr_gap
            best_match = Create_Match(team_red, team_blue, best_gap, total_autofill=0)

    # --- Step 3: 返回 MMR Gap 最小且 autofill=0 的最佳对局 ---
    return best_match
```
