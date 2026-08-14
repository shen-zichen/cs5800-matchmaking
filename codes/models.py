"""
CS 5800 Final Project: MOBA Matchmaking — Core Data Models

This module defines the core data structures used across the three matching stages:
- Lane (Enum): the 5 lane positions (TOP, JUG, MID, ADC, SUP)
- Player (Dataclass): a single player's info and preferences
- Pool (Dataclass): the 10-player candidate pool extracted in Stage 1
- Team (Dataclass): a 5-player laned team
- Match (Dataclass): the final 5v5 match result

For detailed documentation, see the file in the same directory:
code/models_readme.md
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional


class Lane(Enum):
    """The 5 lane positions"""
    TOP = "TOP"
    JUG = "JUG"
    MID = "MID"
    ADC = "ADC"
    SUP = "SUP"


@dataclass
class Player:
    """
    Player model

    Attributes:
        id: player ID
        mmr: hidden matchmaking rating (integer int)
        pref_primary: primary preferred lane
        pref_secondary: secondary preferred lane (optional)
        assigned_lane: the lane assigned after matching (initially None)
        is_autofilled: autofill status (None: not yet determined, True: autofilled, False: got primary/secondary)
    """
    id: str
    mmr: int
    pref_primary: Lane
    pref_secondary: Optional[Lane] = None
    assigned_lane: Optional[Lane] = None
    is_autofilled: Optional[bool] = None


@dataclass
class Pool:
    """The 10-player candidate pool extracted in Stage 1"""
    players: List[Player]


@dataclass
class Team:
    """5-player team model"""
    players: List[Player]
    lane_map: Dict[Lane, Player] = field(default_factory=dict)
    autofill_count: int = 0


@dataclass
class Match:
    """Final 5v5 match model"""
    team_red: Team
    team_blue: Team
    mmr_gap: float = 0.0
    total_autofill: int = 0