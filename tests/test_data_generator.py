"""
Data generator tests.

The generator's one job is the preference-diversity knob (`concentration`):
0 -> lanes uniform (spread), 1 -> hot lanes (MID/ADC) dominate (clumped). Plus
some hygiene guarantees the experiment relies on: clean ids, distinct pref
pair, MMR in range, and reproducibility under a fixed seed.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from collections import Counter
from codes.models import Lane, Player
from codes.data_generator import (
    generate_players,
    generate_snapshot,
    _lane_weights,
    HOT_LANES,
    COLD_LANES,
)


# ---------- the knob: weights ----------

def test_weights_sum_to_one_across_knob():
    """Whatever the knob, the 5 lane weights form a valid distribution (sum 1)."""
    for conc in [0.0, 0.25, 0.5, 0.75, 1.0]:
        assert sum(_lane_weights(conc)) == pytest.approx(1.0)


def test_knob_zero_is_uniform():
    """concentration=0 -> every lane equally likely (0.2 each)."""
    weights = _lane_weights(0.0)
    for w in weights:
        assert w == pytest.approx(0.2)


def test_knob_one_zeros_out_cold_lanes():
    """concentration=1 -> cold lanes get 0 weight, all weight on hot lanes."""
    weights = dict(zip(list(Lane), _lane_weights(1.0)))
    for lane in COLD_LANES:
        assert weights[lane] == pytest.approx(0.0)
    for lane in HOT_LANES:
        assert weights[lane] > 0.0


# ---------- the knob: actual generated preferences ----------

def test_higher_concentration_means_more_hot_primary():
    """
    Empirical direction check: more concentration -> more players whose PRIMARY
    is a hot lane. Uses a big sample + fixed seed so the count is stable.
    """
    def hot_primary_count(conc):
        players = generate_players(1000, concentration=conc, seed=7)
        return sum(1 for p in players if p.pref_primary in HOT_LANES)

    low = hot_primary_count(0.0)
    mid = hot_primary_count(0.5)
    high = hot_primary_count(1.0)
    assert low < mid < high
    assert high == 1000  # at conc=1 every primary is hot


def test_knob_zero_spreads_across_all_lanes():
    """concentration=0 -> all five lanes actually appear as primary."""
    players = generate_players(1000, concentration=0.0, seed=7)
    seen = {p.pref_primary for p in players}
    assert seen == set(Lane)


# ---------- hygiene guarantees ----------

def test_ids_are_clean():
    """ids have no whitespace and are the expected P00.. format."""
    players = generate_players(10, seed=1)
    for i, p in enumerate(players):
        assert p.id == f"P{i:02d}"
        assert p.id == p.id.strip()          # no leading/trailing space
        assert " " not in p.id


def test_primary_and_secondary_are_distinct():
    """Every player has two DIFFERENT preferred lanes (LOCKED: both filled)."""
    for conc in [0.0, 0.5, 1.0]:
        players = generate_players(200, concentration=conc, seed=3)
        for p in players:
            assert p.pref_primary is not None
            assert p.pref_secondary is not None
            assert p.pref_primary != p.pref_secondary


def test_mmr_within_range():
    """MMR stays inside the requested [low, high]."""
    players = generate_players(500, mmr_low=1200, mmr_high=1800, seed=9)
    for p in players:
        assert 1200 <= p.mmr <= 1800


def test_count_matches_request():
    """generate_players(n) returns exactly n players."""
    assert len(generate_players(37, seed=1)) == 37


def test_seed_is_reproducible():
    """Same seed -> identical snapshot (needed for reproducible experiments)."""
    a = generate_players(20, concentration=0.4, seed=123)
    b = generate_players(20, concentration=0.4, seed=123)
    for pa, pb in zip(a, b):
        assert pa.id == pb.id
        assert pa.mmr == pb.mmr
        assert pa.pref_primary == pb.pref_primary
        assert pa.pref_secondary == pb.pref_secondary


def test_different_seed_differs():
    """Different seeds -> different data (sanity: seed actually matters)."""
    a = generate_players(20, concentration=0.4, seed=1)
    b = generate_players(20, concentration=0.4, seed=2)
    a_mmrs = [p.mmr for p in a]
    b_mmrs = [p.mmr for p in b]
    assert a_mmrs != b_mmrs


def test_snapshot_default_size():
    """generate_snapshot defaults to a 50-player queue."""
    assert len(generate_snapshot()) == 50


if __name__ == "__main__":
    tests = [
        ("weights sum to 1", test_weights_sum_to_one_across_knob),
        ("knob=0 uniform", test_knob_zero_is_uniform),
        ("knob=1 zeros cold", test_knob_one_zeros_out_cold_lanes),
        ("higher conc -> more hot", test_higher_concentration_means_more_hot_primary),
        ("knob=0 spreads all lanes", test_knob_zero_spreads_across_all_lanes),
        ("ids clean", test_ids_are_clean),
        ("pref pair distinct", test_primary_and_secondary_are_distinct),
        ("mmr in range", test_mmr_within_range),
        ("count matches", test_count_matches_request),
        ("seed reproducible", test_seed_is_reproducible),
        ("different seed differs", test_different_seed_differs),
        ("snapshot default 50", test_snapshot_default_size),
    ]
    passed = 0
    for name, fn in tests:
        try:
            fn(); print(f"PASS  {name}"); passed += 1
        except Exception as e:
            import traceback
            print(f"FAIL  {name} -> {e}\n{traceback.format_exc()}")
    print(f"\n{passed}/{len(tests)} passed")