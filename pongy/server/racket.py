from dataclasses import dataclass
from random import randint
from typing import Protocol

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import RacketSide
from pongy.server.ball import IBall


class IRacket(Protocol):
    position: int
    side: RacketSide

    def hit(self, ball: IBall) -> None:
        pass

    def move(self, direction: MoveDirection) -> None:
        pass

    def reset(self) -> None:
        pass


@dataclass
class BaseRacket:
    position: int = (settings.BOARD_SIZE - settings.RACKET_LENGTH) // 2
    side: RacketSide = RacketSide.BOTTOM

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


class BottomRacket(BaseRacket):
    side: RacketSide = RacketSide.BOTTOM

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


class TopRacket(BaseRacket):
    side: RacketSide = RacketSide.TOP

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


class LeftRacket(BaseRacket):
    side: RacketSide = RacketSide.LEFT

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


class RightRacket(BaseRacket):
    side: RacketSide = RacketSide.RIGHT

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
