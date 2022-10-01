from dataclasses import dataclass
from random import randint
from typing import Protocol

from pongy import settings
from pongy.models import BoardSide
from pongy.models import MoveDirection
from pongy.models import WsRacket
from pongy.server.ball import IBall


class IRacket(Protocol):
    position: int
    side: BoardSide

    def hit(self, ball: IBall) -> None:
        pass

    def move(self, direction: MoveDirection) -> None:
        pass

    def reset(self) -> None:
        pass

    def to_payload(self) -> WsRacket:
        pass


@dataclass
class BaseRacket:
    position: int = (settings.BOARD_SIZE - settings.RACKET_LENGTH) // 2
    side: BoardSide = BoardSide.BOTTOM

    def hit(self, ball: IBall) -> None:
        pass

    def reset(self) -> None:
        self.position = (settings.BOARD_SIZE - settings.RACKET_LENGTH) // 2

    def move(self, direction: MoveDirection) -> None:
        if direction == MoveDirection.LEFT:
            if self.position - settings.RACKET_SPEED >= 0:
                self.position -= settings.RACKET_SPEED
            else:
                self.position = 0
        if direction == MoveDirection.RIGHT:
            if (
                self.position + settings.RACKET_SPEED
                <= settings.BOARD_SIZE - settings.RACKET_LENGTH
            ):
                self.position += settings.RACKET_SPEED
            else:
                self.position = settings.BOARD_SIZE - settings.RACKET_LENGTH

    def to_payload(self) -> WsRacket:
        return WsRacket(
            position=self.position,
            side=self.side,
        )


@dataclass
class BottomRacket(BaseRacket):
    side: BoardSide = BoardSide.BOTTOM

    def hit(self, ball: IBall) -> None:
        new_x, new_y = ball.position
        if (
            new_y > settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            and self.position - settings.BALL_SIZE
            < new_x
            < self.position + settings.RACKET_LENGTH + settings.BALL_SIZE
        ):
            new_y = settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            ball.angle = randint(200, 340)
            ball.change_speed()
        ball.position = int(new_x), int(new_y)


@dataclass
class TopRacket(BaseRacket):
    side: BoardSide = BoardSide.TOP

    def hit(self, ball: IBall) -> None:
        new_x, new_y = ball.position
        if (
            new_y < settings.RACKET_HEIGHT
            and self.position - settings.BALL_SIZE
            < new_x
            < self.position + settings.RACKET_LENGTH + settings.BALL_SIZE
        ):
            new_y = settings.RACKET_HEIGHT
            ball.angle = randint(20, 160)
            ball.change_speed()
        ball.position = int(new_x), int(new_y)


@dataclass
class LeftRacket(BaseRacket):
    side: BoardSide = BoardSide.LEFT

    def hit(self, ball: IBall) -> None:
        new_x, new_y = ball.position
        if (
            new_x < settings.RACKET_HEIGHT
            and self.position - settings.BALL_SIZE
            < new_y
            < self.position + settings.RACKET_LENGTH + settings.BALL_SIZE
        ):
            new_x = settings.RACKET_HEIGHT
            ball.angle = randint(-70, 70)
            ball.change_speed()
        ball.position = int(new_x), int(new_y)


@dataclass
class RightRacket(BaseRacket):
    side: BoardSide = BoardSide.RIGHT

    def hit(self, ball: IBall) -> None:
        new_x, new_y = ball.position
        if (
            new_x > settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            and self.position - settings.BALL_SIZE
            < new_y
            < self.position + settings.RACKET_LENGTH + settings.BALL_SIZE
        ):
            new_x = settings.BOARD_SIZE - settings.BALL_SIZE - settings.RACKET_HEIGHT
            ball.angle = randint(110, 250)
            ball.change_speed()
        ball.position = int(new_x), int(new_y)
