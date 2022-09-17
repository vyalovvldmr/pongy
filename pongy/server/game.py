import asyncio
import logging
import math
from random import randint
from types import TracebackType

from aiohttp import web

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import WsEvent
from pongy.models import WsGameStateEvent
from pongy.models import WsGameStatePayload
from pongy.models import WsPlayer


logger = logging.getLogger(__name__)


class Player:
    def __init__(self, uuid: str, ws: web.WebSocketResponse):
        self.uuid: str = uuid
        self.ws: web.WebSocketResponse = ws
        self.score: int = 0
        self.racket_position: int = 325

    def move_racket(self, direction: MoveDirection) -> None:
        if (
            direction == MoveDirection.LEFT
            and self.racket_position - settings.RACKET_SPEED >= 0
        ):
            self.racket_position -= settings.RACKET_SPEED
        if (
            direction == MoveDirection.RIGHT
            and self.racket_position + settings.RACKET_SPEED
            <= settings.BOARD_SIZE[0] - settings.RACKET_LENGTH
        ):
            self.racket_position += settings.RACKET_SPEED


class Game:
    def __init__(self) -> None:
        self.players: list[Player] = []
        self.ball_position: tuple[int, int] = (345, 345)
        self.ball_angle: int = randint(0, 360)
        self._broadcaster = asyncio.ensure_future(self.broadcast())

    def add_player(self, player: Player) -> None:
        self.players.append(player)

    def remove_player(self, player: Player) -> None:
        self.players[:] = [p for p in self.players if p.uuid != player.uuid]
        if not self.players:
            self._broadcaster.cancel()

    def move_ball(self) -> None:
        new_x = self.ball_position[0] + settings.BALL_SPEED * math.cos(
            math.radians(self.ball_angle)
        )
        new_y = self.ball_position[1] + settings.BALL_SPEED * math.sin(
            math.radians(self.ball_angle)
        )
        if new_x < 0:
            new_x = 0
            self.ball_angle = 180 - self.ball_angle
        elif new_x > settings.BOARD_SIZE[0] - 10:
            new_x = settings.BOARD_SIZE[0] - 10
            self.ball_angle = 180 - self.ball_angle
        if new_y < 0:
            new_y = 0
            self.ball_angle = -self.ball_angle
        elif new_y > settings.BOARD_SIZE[0] - 10:
            new_y = settings.BOARD_SIZE[0] - 10
            self.ball_angle = -self.ball_angle
        self.ball_position = int(new_x), int(new_y)

    def to_payload(self) -> WsGameStatePayload:
        return WsGameStatePayload(
            ball_position=self.ball_position,
            players=[
                WsPlayer(
                    uuid=player.uuid,
                    score=player.score,
                    racket_position=player.racket_position,
                )
                for player in self.players
            ],
        )

    async def broadcast(self):
        while True:
            await self.publish_state()
            await asyncio.sleep(0.05)
            self.move_ball()

    async def publish_state(self) -> None:
        payload = WsEvent(data=WsGameStateEvent(payload=self.to_payload()))
        for subscriber in self.players:
            try:
                await subscriber.ws.send_json(payload.dict())
            except ConnectionResetError as err:
                logger.warning(err)


class GamePool:
    _awaiting: Game | None = None

    def __init__(self, player: Player) -> None:
        self._player: Player = player
        self._game: Game | None = None

    async def __aenter__(self) -> Game:
        if not GamePool._awaiting:
            self._game = GamePool._awaiting = Game()
        else:
            self._game = GamePool._awaiting
        self._game.add_player(self._player)
        if len(self._game.players) == 4:
            GamePool._awaiting = None
        return self._game

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._game:
            self._game.remove_player(self._player)
            if GamePool._awaiting is self._game and not self._game.players:
                GamePool._awaiting = None
