from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class State(str, Enum):
    IDLE = "idle"
    AWAITING_TOTAL = "awaiting_total"
    AWAITING_MODE = "awaiting_mode"
    AWAITING_PLAYER_COUNT = "awaiting_player_count"
    AWAITING_PLAYERS = "awaiting_players"


class SplitMode(str, Enum):
    EQUAL = "equal"
    HOURS = "hours"
    CUSTOM = "custom"


@dataclass
class Session:
    state: State = State.IDLE
    total: Optional[float] = None
    mode: Optional[SplitMode] = None
    n_players: Optional[int] = None
    players: list = field(default_factory=list)


_sessions: dict[str, Session] = {}


def get_session(source_id: str) -> Session:
    if source_id not in _sessions:
        _sessions[source_id] = Session()
    return _sessions[source_id]


def reset_session(source_id: str) -> Session:
    _sessions[source_id] = Session()
    return _sessions[source_id]
