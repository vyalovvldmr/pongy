from aiohttp import web

from pongy.server.racket import BaseRacket
from pongy.server.racket import IRacket


class Player:
    def __init__(self, uuid: str, ws: web.WebSocketResponse):
        self.uuid: str = uuid
        self.ws: web.WebSocketResponse = ws
        self.score: int = 0
        self.racket: IRacket = BaseRacket()
