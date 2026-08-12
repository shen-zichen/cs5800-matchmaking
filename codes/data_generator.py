"""
CS 5800 Final Project: MOBA Matchmaking - Synthetic Data Generator

Generates queue snapshots of players for the comparison experiment. The single
independent variable is `concentration` (the "preference diversity knob"):

    concentration = 0.0  -> every lane equally likely (preferences SPREAD OUT)
    concentration = 1.0  -> hot lanes dominate, cold lanes almost never picked
                            (preferences CLUMPED -> forces autofill downstream)

MMR is generated independently of concentration (skill and lane-preference are
separate player attributes). Player.id is clean (no whitespace), per the LOCKED
id convention, so the two pipelines' results can be joined by id.
"""

import random
from typing import List, Optional
from codes.models import Lane, Player, Pool


# Lanes split into "hot" (carry roles everyone wants) and "cold" (JUG/SUP).
# Fixed on purpose: the experiment's variable is HOW clumped, not WHICH lanes
# are hot. Keeping this fixed makes runs reproducible.
HOT_LANES = [Lane.MID, Lane.ADC]
COLD_LANES = [Lane.TOP, Lane.JUG, Lane.SUP]
ALL_LANES = list(Lane)


def _lane_weights(concentration: float) -> List[float]:
    """
    Build a pick-probability weight for each of the 5 lanes from the knob.

    Think of it as stuffing a bag with lane tickets:
    - concentration = 0 -> every lane gets an equal share (uniform bag).
    - concentration = 1 -> all the weight piles onto the hot lanes; cold lanes
      get (almost) none.

    Implementation: start uniform, then shift `concentration` worth of weight
    from the cold lanes onto the hot lanes. Returns weights in ALL_LANES order.
    """
    n = len(ALL_LANES)
    base = 1.0 / n  # uniform share per lane

    weights = []
    for lane in ALL_LANES:
        if lane in HOT_LANES:
            # hot lanes: base share plus a bonus that grows with the knob,
            # split evenly across the hot lanes.
            bonus = concentration * (len(COLD_LANES) / n) / len(HOT_LANES)
            weights.append(base + bonus)
        else:
            # cold lanes: their share is dialed down toward 0 as the knob rises.
            weights.append(base * (1.0 - concentration))
    return weights


def _pick_two_distinct_lanes(concentration: float, rng: random.Random):
    """
    Pick a (primary, secondary) lane pair. Both are always filled (LOCKED: every
    player has primary + secondary) and must be distinct. The knob biases the
    choice toward hot lanes; secondary is re-drawn until it differs from primary.
    """
    weights = _lane_weights(concentration)
    primary = rng.choices(ALL_LANES, weights=weights, k=1)[0]
    secondary = rng.choices(ALL_LANES, weights=weights, k=1)[0]
    while secondary == primary:
        secondary = rng.choices(ALL_LANES, weights=weights, k=1)[0]
    return primary, secondary


def generate_players(
    n: int,
    concentration: float = 0.0,
    mmr_low: int = 1000,
    mmr_high: int = 2000,
    seed: Optional[int] = None,
) -> List[Player]:
    """
    Generate `n` players.

    Args:
        n: how many players.
        concentration: 0..1 preference-diversity knob (0 spread, 1 clumped).
        mmr_low, mmr_high: MMR drawn uniformly in [mmr_low, mmr_high].
        seed: optional RNG seed for reproducible snapshots.

    Returns:
        a list of n Players with clean ids "P00", "P01", ...
    """
    rng = random.Random(seed)
    players = []
    for i in range(n):
        primary, secondary = _pick_two_distinct_lanes(concentration, rng)
        players.append(Player(
            id=f"P{i:02d}",                       # clean id, no whitespace
            mmr=rng.randint(mmr_low, mmr_high),
            pref_primary=primary,
            pref_secondary=secondary,
        ))
    return players


def generate_snapshot(
    n: int = 50,
    concentration: float = 0.0,
    seed: Optional[int] = None,
) -> List[Player]:
    """
    One queue snapshot: a pool of `n` waiting players (default 50) that Stage 1
    pooling will slide a window over. This is the unit the experiment feeds in.
    """
    return generate_players(n=n, concentration=concentration, seed=seed)