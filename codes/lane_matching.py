"""
CS 5800 Final Project: MOBA Matchmaking — Lane Matching Engine

This module implements a pure-Python, hand-written Edmonds-Karp Max-Flow lane matching algorithm.
It mainly contains:
- MatchingGraph: a minimal flow-network graph data structure
- solve_lane_matching: the main entry point for solving Max-Flow matching on a 5v5 team or a 10-player pool
- handle_autofill: assigns a fallback lane to players who did not get their primary/secondary preference
- a family of convenience API getter wrappers (get_matching, get_autofill_count, get_max_flow_count, etc.)

For details see: docs/lane_matching_api_contract.md and docs/lane_matching_draft_Liuyi.md
"""

import copy
import os
import sys
from collections import deque
from typing import List, Dict, Tuple, Optional

# Ensure the project root is on sys.path so this script can be run directly from any directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codes.models import Lane, Player

# Define the unified constant list of the 5 standard lanes (derived automatically from the Lane enum)
ALL_LANES = [lane.value for lane in Lane]


class MatchingGraph:
    """
    Matching graph data structure (implemented with plain native Python dicts)
    Uses self.edge_dict[u][v] = [cap, flow, is_original] to store edge info
    """
    def __init__(self):
        self.edge_dict: Dict[str, Dict[str, list]] = {}

    def add_node(self, u: str):
        if u not in self.edge_dict:
            self.edge_dict[u] = {}

    def add_edge(self, u: str, v: str, cap: int):
        """Add an edge: forward original edge marked True, reverse residual edge marked False"""
        self.add_node(u)
        self.add_node(v)
        # Forward original edge: [capacity cap, initial flow 0, is_original True]
        self.edge_dict[u][v] = [cap, 0, True]
        # Reverse residual edge: [capacity 0, initial flow 0, is_original False]
        self.edge_dict[v][u] = [0, 0, False]

    def get_neighbors(self, u: str):
        """Get the list of all neighbor nodes of node u (Python 3.7+ dicts preserve key insertion order)"""
        return self.edge_dict.get(u, {}).keys()

    def get_residual_capacity(self, u: str, v: str) -> int:
        """Get the residual capacity"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # Forward original edge: remaining capacity = cap - flow
            return cap - flow
        else:
            # Reverse residual edge: remaining residual capacity = the actual flow on the forward edge
            return self.edge_dict[v][u][1]

    def augment(self, u: str, v: str, bottleneck: int):
        """Push/cancel flow along (u, v) to update the flow"""
        cap, flow, is_original = self.edge_dict[u][v]
        if is_original:
            # Forward edge: flow increases
            self.edge_dict[u][v][1] += bottleneck
        else:
            # Reverse edge: the forward edge's flow decreases (cancel flow!)
            self.edge_dict[v][u][1] -= bottleneck


def reconstruct_path(parent: Dict[str, Optional[str]], s: str, t: str) -> List[str]:
    """
    Trace back from sink t to source s along the parent dict
    Returns the reconstructed path list, e.g. ['s', 'P1', 'TOP', 't']
    """
    path = []
    curr: Optional[str] = t
    
    # As long as the current node is not None, keep tracing up to the parent
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)  # get the parent of the current node
        
    # Python lists have a built-in reverse() method; reverse to get order from s to t
    path.reverse()
    return path


def update_flow_along_path(path: List[str], graph: MatchingGraph) -> int:
    """
    Step 1: compute the bottleneck capacity along the whole path
    Step 2: update each edge's triple (flow and residual capacity) along the path
    Returns: the amount of flow added this time (equals 1 in bipartite matching)
    """
    # 1. Iterate over each adjacent pair (u, v) on the path and find the minimum residual capacity (bottleneck)
    bottleneck: int = 999999
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        c_f = graph.get_residual_capacity(u, v)  # get the current residual capacity of (u, v)
        bottleneck = min(bottleneck, c_f)
        
    # 2. With the bottleneck value, iterate the path again and update each edge's triple state
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        graph.augment(u, v, bottleneck)  # push bottleneck along (u, v)
        
    return bottleneck  # in a bipartite matching network, the return value equals 1


def bfs_find_path(matching_graph: MatchingGraph, s: str, t: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Use BFS to find the augmenting path with the fewest edges from s to t in the residual network
    Returns the parent dict; returns None if no valid path from s to t is found
    """
    # Record each node's parent (the guide); the source s has parent None
    parent: Dict[str, Optional[str]] = {s: None}
    queue = deque([s])
    
    # Keep searching while the queue is non-empty and the sink t has not been reached
    while queue and t not in parent:
        curr = queue.popleft()
        
        # Iterate over all neighbor nodes nxt of curr
        for nxt in matching_graph.get_neighbors(curr):
            # Check 1: residual capacity must be > 0 (can still push or cancel flow)
            # Check 2: nxt has not been visited yet (prevents infinite loops / backtracking)
            if nxt not in parent and matching_graph.get_residual_capacity(curr, nxt) > 0:
                parent[nxt] = curr
                queue.append(nxt)
                
    # Check whether a path reaching the sink t was successfully found
    if t in parent:
        return parent
    else:
        return None  # no augmenting path from s to t exists in the residual network anymore


def build_matching_graph(players: List[Player], lane_capacity: int = 1) -> MatchingGraph:
    """
    Initialize and build the bipartite matching flow network graph MatchingGraph
    """
    matching_graph = MatchingGraph()
    s = "s"
    t = "t"

    # 1. Connect source s to all players (capacity 1)
    for p in players:
        matching_graph.add_edge(s, p.id, cap=1)

    # 2. Connect players to preferred lanes (primary always present, secondary optional; both capacity 1)
    for p in players:
        matching_graph.add_edge(p.id, p.pref_primary.value, cap=1)
        # Defensive check and log hint: handle players with no secondary lane (None)
        if p.pref_secondary is not None:
            matching_graph.add_edge(p.id, p.pref_secondary.value, cap=1)
        else:
            print(f"[Info] Player {p.id} has no secondary lane (pref_secondary is None); only the primary lane edge is connected.")

    # 3. Connect the 5 lanes to sink 't' (capacity lane_capacity: 1 for a 5-player team, 2 for a 10-player pool)
    for lane_name in ALL_LANES:
        matching_graph.add_edge(lane_name, t, cap=lane_capacity)

    return matching_graph


def handle_autofill(unmatched_players: List[Player], matching: Dict[str, str], lane_counts: Dict[str, int], lane_capacity: int):
    """
    Autofill players who could not be matched to a preferred lane into open lane slots
    """
    for p in unmatched_players:
        # Defensive guard: safely return None when all lanes have reached capacity
        open_lane = next((lane_name for lane_name in ALL_LANES if lane_counts[lane_name] < lane_capacity), None)
        if open_lane is None:
            break
        matching[p.id] = open_lane
        p.assigned_lane = Lane(open_lane)  # assign uniformly as a Lane enum object
        p.is_autofilled = True
        lane_counts[open_lane] += 1


def solve_lane_matching(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int, int]:
    """
    The single main entry point of the pure-Python Max-Flow lane matching algorithm
    
    Args:
        players: list of players (a 5-player team or a 10-player pool)
        lane_capacity: capacity upper bound per lane (1 for a 5-player team, 2 for a 10-player pool)
    Returns:
        (matching, autofill_count, max_flow)
        - matching: the matching map dict {player_id: assigned_lane_name}
        - autofill_count: the number of players who had to be autofilled
        - max_flow: the total number of players successfully matched to a preferred lane
    """
    # 1. Deep-copy the incoming player list to avoid modifying the original objects
    players_working = copy.deepcopy(players)

    # 2. Call the graph initialization function
    matching_graph = build_matching_graph(players_working, lane_capacity)
    s = "s"
    t = "t"

    # 3. Edmonds-Karp main loop: solve Max-Flow
    max_flow = 0
    parent = bfs_find_path(matching_graph, s, t)
    while parent is not None:
        path = reconstruct_path(parent, s, t)
        update_flow_along_path(path, matching_graph)
        max_flow += 1
        parent = bfs_find_path(matching_graph, s, t)

    # 4. Extract the matching result
    matching = {}
    lane_counts = {lane_name: 0 for lane_name in ALL_LANES}
    unmatched_players = []

    for p in players_working:
        # Use a Python generator to find whether this player has a matched lane with flow == 1
        matched_lane = next(
            (lane_name for lane_name in ALL_LANES 
             if lane_name in matching_graph.edge_dict.get(p.id, {}) 
             and matching_graph.edge_dict[p.id][lane_name][1] == 1), 
            None
        )
        if matched_lane:
            matching[p.id] = matched_lane
            p.assigned_lane = Lane(matched_lane)  # assign uniformly as a Lane enum object
            p.is_autofilled = False
            lane_counts[matched_lane] += 1
        else:
            unmatched_players.append(p)

    # 4. If max_flow did not reach the total player count (i.e. there is a lane gap), trigger Autofill
    expected_flow = len(players)
    if max_flow < expected_flow:
        handle_autofill(unmatched_players, matching, lane_counts, lane_capacity)
        autofill_count = expected_flow - max_flow
    else:
        autofill_count = 0

    # Return the unified triple
    return matching, autofill_count, max_flow


# --- API Wrapper Functions ---

def get_matching(players: List[Player], lane_capacity: int = 1) -> Dict[str, str]:
    """
    API: get only the lane matching map dict
    Returns: matching (dict) -> {player_id: assigned_lane_name}
    """
    matching, _, _ = solve_lane_matching(players, lane_capacity)
    return matching


def get_autofill_count(players: List[Player], lane_capacity: int = 1) -> int:
    """
    API: get only the autofill player count
    Returns: autofill_count (int)
    """
    _, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return autofill_count


def get_max_flow_count(players: List[Player], lane_capacity: int = 1) -> int:
    """
    API: get only the Max-Flow count of players successfully matched to a preference (used for feasibility checks)
    Returns: max_flow_count (int)
    """
    _, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return max_flow_count


def get_matching_and_autofill_count(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int]:
    """
    Combined API: get the matching map dict and the autofill player count
    Returns: (matching, autofill_count)
    """
    matching, autofill_count, _ = solve_lane_matching(players, lane_capacity)
    return matching, autofill_count


def get_matching_and_max_flow_count(players: List[Player], lane_capacity: int = 1) -> Tuple[Dict[str, str], int]:
    """
    Combined API: get the matching map dict and the Max-Flow value
    Returns: (matching, max_flow_count)
    """
    matching, _, max_flow_count = solve_lane_matching(players, lane_capacity)
    return matching, max_flow_count