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
        self.racket_position: int = (settings.BOARD_SIZE - settings.RACKET_LENGTH) // 2

    def move_racket(self, direction: MoveDirection) -> None:
        if (
            direction == MoveDirection.LEFT
            and self.racket_position - settings.RACKET_SPEED >= 0
        ):
            self.racket_position -= settings.RACKET_SPEED
        if (
            direction == MoveDirection.RIGHT
            and self.racket_position + settings.RACKET_SPEED
            <= settings.BOARD_SIZE - settings.RACKET_LENGTH
        ):
            self.racket_position += settings.RACKET_SPEED


class Game:
    def __init__(self) -> None:
        self.players: list[Player] = []
        self.ball_position: tuple[int, int] = (
            (settings.BOARD_SIZE - settings.BALL_SIZE) // 2,
        ) * 2
        self.ball_angle: int = randint(20, 160)
        self.ball_speed: int = settings.DEFAULT_BALL_SPEED
        self._run_task = asyncio.ensure_future(self.run())

    def add_player(self, player: Player) -> None:
        self.players.append(player)

    def remove_player(self, player: Player) -> None:
        self.players[:] = [p for p in self.players if p.uuid != player.uuid]
        if self.is_empty:
            self._run_task.cancel()

    def move_ball(self) -> None:
        new_x = self.ball_position[0] + self.ball_speed * math.cos(
            math.radians(self.ball_angle)
        )
        new_y = self.ball_position[1] + self.ball_speed * math.sin(
            math.radians(self.ball_angle)
        )
        self.ball_position = int(new_x), int(new_y)

    def hit(self) -> None:
        new_x, new_y = self.ball_position
        if (
            len(self.players) > 0
            and new_y
            > settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            and self.players[0].racket_position - settings.BALL_SIZE
            < new_x
            < self.players[0].racket_position
            + settings.RACKET_LENGTH
            + settings.BALL_SIZE
        ):
            new_y = settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            self.ball_angle = randint(200, 340)
            self.change_ball_speed()
        if (
            len(self.players) > 1
            and new_y < settings.RACKET_HEIGHT
            and self.players[1].racket_position - settings.BALL_SIZE
            < new_x
            < self.players[1].racket_position
            + settings.RACKET_LENGTH
            + settings.BALL_SIZE
        ):
            new_y = settings.RACKET_HEIGHT
            self.ball_angle = randint(20, 160)
            self.change_ball_speed()
        if (
            len(self.players) > 2
            and new_x < settings.RACKET_HEIGHT
            and self.players[2].racket_position - settings.BALL_SIZE
            < new_y
            < self.players[2].racket_position
            + settings.RACKET_LENGTH
            + settings.BALL_SIZE
        ):
            new_x = settings.RACKET_HEIGHT
            self.ball_angle = randint(-70, 70)
            self.change_ball_speed()
        if (
            len(self.players) > 3
            and new_x
            > settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            and self.players[3].racket_position - settings.BALL_SIZE
            < new_y
            < self.players[3].racket_position
            + settings.RACKET_LENGTH
            + settings.BALL_SIZE
        ):
            new_x = settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            self.ball_angle = randint(110, 250)
            self.change_ball_speed()
        self.ball_position = int(new_x), int(new_y)

    def bounce(self) -> None:
        new_x, new_y = self.ball_position
        if new_x < 0:
            new_x = 0
            self.ball_angle = 180 - self.ball_angle
            if len(self.players) > 2:
                self.players[2].score += 1
        elif new_x > settings.BOARD_SIZE - settings.BALL_SIZE:
            new_x = settings.BOARD_SIZE - settings.BALL_SIZE
            self.ball_angle = 180 - self.ball_angle
            if len(self.players) > 3:
                self.players[3].score += 1
        if new_y < 0:
            new_y = 0
            self.ball_angle = -self.ball_angle
            if len(self.players) > 1:
                self.players[1].score += 1
        elif new_y > settings.BOARD_SIZE - settings.BALL_SIZE:
            new_y = settings.BOARD_SIZE - settings.BALL_SIZE
            self.ball_angle = -self.ball_angle
            if len(self.players) > 0:
                self.players[0].score += 1
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

    async def run(self) -> None:
        while True:
            await self.broadcast()
            await asyncio.sleep(1 / settings.FPS)
            self.move_ball()
            self.hit()
            self.bounce()

    async def broadcast(self) -> None:
        payload = WsEvent(data=WsGameStateEvent(payload=self.to_payload()))
        await asyncio.gather(
            *(subscriber.ws.send_json(payload.dict()) for subscriber in self.players)
        )

    @property
    def is_full(self) -> bool:
        return len(self.players) == 4

    @property
    def is_empty(self) -> bool:
        return not self.players

    def change_ball_speed(self) -> None:
        self.ball_speed = randint(settings.MIN_BALL_SPPED, settings.MAX_BALL_SPPED)


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
        if self._game.is_full:
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
