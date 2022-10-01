from dataclasses import dataclass
from typing import Protocol

from aiohttp import web

from pongy.models import BoardSide
from pongy.server.racket import BaseRacket
from pongy.server.racket import IRacket


class IPlayer(Protocol):
    uuid: str
    ws: web.WebSocketResponse
    score: int
    racket: IRacket

    def bounce_notify(self, side: BoardSide) -> None:
        pass


@dataclass
class Player:
    uuid: str
    ws: web.WebSocketResponse
    score: int = 0
    racket: IRacket = BaseRacket()

    def bounce_notify(self, side: BoardSide) -> None:
        if self.racket.side == side:
            self.score += 1
