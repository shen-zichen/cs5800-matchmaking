"""
CS 5800 期末项目：MOBA Matchmaking — 核心数据模型

本模块定义了匹配算法三阶段用到的核心数据结构：
- Lane (Enum): 5 个分路位置 (TOP, JUG, MID, ADC, SUP)
- Player (Dataclass): 单个玩家信息与偏好
- Pool (Dataclass): Stage 1 抽取出的 10 人候选池
- Team (Dataclass): 5 人分路队伍
- Match (Dataclass): 最终 5v5 对局结果

详细说明文档请参考同目录下的：
code/models_readme.md
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional


class Lane(Enum):
    """5 个分路位置"""
    TOP = "TOP"
    JUG = "JUG"
    MID = "MID"
    ADC = "ADC"
    SUP = "SUP"


@dataclass
class Player:
    """
    玩家模型
    
    Attributes:
        id: 玩家 ID
        mmr: 隐藏战力分 (整数 int)
        pref_primary: 主选分路
        pref_secondary: 次选分路 (可选)
        assigned_lane: 匹配后分派的分路 (初始为 None)
        is_autofilled: 补位状态 (None: 尚未判断, True: 被补位, False: 满足主/次选)
    """
    id: str
    mmr: int
    pref_primary: Lane
    pref_secondary: Optional[Lane] = None
    assigned_lane: Optional[Lane] = None
    is_autofilled: Optional[bool] = None


@dataclass
class Pool:
    """Stage 1 抽出的 10 人候选池"""
    players: List[Player]


@dataclass
class Team:
    """5 人队伍模型"""
    players: List[Player]
    lane_map: Dict[Lane, Player] = field(default_factory=dict)
    autofill_count: int = 0


@dataclass
class Match:
    """最终 5v5 对局模型"""
    team_red: Team
    team_blue: Team
    mmr_gap: float = 0.0
    total_autofill: int = 0
