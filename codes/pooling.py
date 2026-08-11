from typing import List, Optional
from codes.models import Player, Pool
from codes.lane_matching import get_max_flow_count


def find_pool(players: List[Player], pool_size: int = 10) -> Optional[Pool]:
    """
    Stage 1 pooling: from a static queue snapshot, find one MMR-compact,
    lane-feasible pool of `pool_size` players via a sliding window.

    Sort players by MMR, then slide a fixed-size window from low to high MMR.
    Return the first window that is lane-feasible; return None if none exists.

    Feasibility is decided ONLY by max_flow == pool_size (see the `if` below),
    never by inspecting assigned_lane — autofill fills lanes even for
    infeasible pools, which would fake a "feasible" result.

    Args:
        players: the snapshot to pool from (not mutated; sorted on a copy).
        pool_size: window width. Fixed at 10 for the comparison experiment
            (5 lanes x 2). Parameterized only for the scalability line.

    Returns:
        A Pool of `pool_size` players, or None if no feasible window exists.
    """
    # sorted() returns a new list; the caller's `players` is left untouched.
    sorted_players = sorted(players, key=lambda p: p.mmr)
    n = len(sorted_players)

    # Slide a fixed-width window over adjacent (MMR-compact) players.
    # Last valid start is n - pool_size; range's exclusive bound needs +1.
    # If n < pool_size, range is empty -> we fall through to `return None`.
    for start in range(0, n - pool_size + 1):
        window = sorted_players[start : start + pool_size]

        # Feasibility oracle: max_flow == pool_size means every lane slot
        # (5 lanes x cap 2 = 10) is filled with a preferred assignment,
        # i.e. autofill_count == 0. Capped at 10, so it can never exceed.
        if get_max_flow_count(window, lane_capacity=2) == pool_size:
            # First feasible window wins — MMR-compactness is guaranteed
            # by the input ordering, so we stop instead of seeking "better".
            return Pool(players=window)

    # Scanned every window, none feasible. Expected outcome (e.g. the
    # experiment deliberately feeds preference-concentrated data), not an error.
    return None