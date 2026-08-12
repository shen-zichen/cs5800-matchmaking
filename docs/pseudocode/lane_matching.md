# Standard Pseudocode: Max-Flow Lane Matching (CLRS Style)

> 📝 **Liuyi 的 Pseudocode 整理笔记**：
> 这份伪代码基于《算法导论》(CLRS 4th Edition Chapter 24) ,核心为其中的 Ford-Fulkerson - Edmonds-Karp (Max-Flow) 网络流模型。
> 我结合项目需求，在教材原版的基础上做了增减、修改等业务落地处理

```python
def Lane_Matching_Max_Flow(P, lane_capacity):
    """
    INPUT: 
        P: List of Players, each with (id, pref_primary, pref_secondary)
        lane_capacity: Integer (1 for 5v5 team, 2 for 10-player pool)
    OUTPUT: 
        matching: Dictionary mapping Player ID to assigned Lane
        autofill_count: Integer (number of players autofilled)
        max_flow: Integer (total flow pushed to sink t)
    """

    # --- Step 1: 构图 (Construct Flow Network G = (V, E)) ---
    G = Create_Empty_Flow_Network()
    for player p in P:
        Add_Directed_Edge(G, s, p, capacity=1)
        Add_Directed_Edge(G, p, p.pref_primary, capacity=1)    # 先加 Primary 边，在 BFS 里形成隐式偏好保护
        Add_Directed_Edge(G, p, p.pref_secondary, capacity=1)  # 后加 Secondary 边

    for lane in {TOP, JUG, MID, ADC, SUP}:
        Add_Directed_Edge(G, lane, t, capacity=lane_capacity)

    # --- Step 2: Edmonds-Karp 主循环 ---
    max_flow = 0
    path = Find_Augmenting_Path_BFS(G, s, t)
    while path is not None:
        for (u, v) in path:
            G.flow(u, v) += 1   # 正向边推流 +1
            G.flow(v, u) -= 1   # 反向边退流 -1 (Undo 撤销改选机制)
        max_flow += 1
        path = Find_Augmenting_Path_BFS(G, s, t)

    # --- Step 3: 匹配结果提取与 Autofill 缺口计算 ---
    matching = {}
    unmatched_players = []
    for player p in P:
        if G.flow(p, p.pref_primary) == 1:
            matching[p.id] = p.pref_primary
        elif G.flow(p, p.pref_secondary) == 1:
            matching[p.id] = p.pref_secondary
        else:
            unmatched_players.append(p)

    autofill_count = len(P) - max_flow
    if autofill_count > 0:
        Assign_Unmatched_Players_To_Remaining_Lanes(unmatched_players, matching, P)

    return matching, autofill_count, max_flow


# --- Helper Function: BFS 找最短增广路 ---
def Find_Augmenting_Path_BFS(G, s, t):
    parent = {}
    queue = FIFO_Queue([s])
    visited = {s}

    while queue is not empty:
        curr = queue.pop_front()
        if curr == t:
            return Reconstruct_Path(parent, s, t)

        for neighbor in G.Neighbors(curr):
            residual_cap = G.capacity(curr, neighbor) - G.flow(curr, neighbor)
            if neighbor not in visited and residual_cap > 0:
                visited.add(neighbor)
                parent[neighbor] = curr
                queue.push_back(neighbor)

    return None
```

## 🔀 跟 CLRS 教材原版伪代码的对比笔记 (By Liuyi)
还没写完 写完了补充