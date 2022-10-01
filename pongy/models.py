from enum import IntEnum
from typing import Literal

from pydantic import BaseModel


class MoveDirection(IntEnum):
    LEFT = 1
    RIGHT = 2


class BoardSide(IntEnum):
    BOTTOM = 1
    TOP = 2
    LEFT = 3
    RIGHT = 4


class WsErrorEventPayload(BaseModel):
    message: str


class WsErrorEvent(BaseModel):
    event: Literal["error"] = "error"
    payload: WsErrorEventPayload


class WsRacket(BaseModel):
    position: int
    side: BoardSide


class WsPlayer(BaseModel):
    uuid: str
    score: int
    racket: WsRacket

    class Config:
        use_enum_values = True


class WsBall(BaseModel):
    position: tuple[int, int]


class WsGameStatePayload(BaseModel):
    players: list[WsPlayer]
    ball: WsBall


class WsGameStateEvent(BaseModel):
    event: Literal["game_state"] = "game_state"
    payload: WsGameStatePayload


class WsEvent(BaseModel):
    data: WsGameStateEvent | WsErrorEvent


class WsCommandMovePayload(BaseModel):
    direction: MoveDirection

    class Config:
        use_enum_values = True


class WsCommand(BaseModel):
    command: Literal["move"] = "move"
    payload: WsCommandMovePayload


class WsCookie(BaseModel):
    player_id: str
