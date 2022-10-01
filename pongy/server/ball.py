import math
from dataclasses import dataclass
from random import randint
from typing import Protocol

from pongy import settings
from pongy.models import WsBall


class IBall(Protocol):
    speed: int
    angle: int
    position: tuple[int, int]

    def move(self) -> None:
        pass

    def change_speed(self) -> None:
        pass

    def to_payload(self) -> WsBall:
        pass


@dataclass
class Ball:
    speed: int = settings.DEFAULT_BALL_SPEED
    angle: int = randint(20, 160)
    position: tuple[int, int] = ((settings.BOARD_SIZE - settings.BALL_SIZE) // 2,) * 2

    def move(self) -> None:
        radians = math.radians(self.angle)
        new_x = self.position[0] + self.speed * math.cos(radians)
        new_y = self.position[1] + self.speed * math.sin(radians)
        self.position = int(new_x), int(new_y)

    def change_speed(self) -> None:
        self.speed = randint(settings.MIN_BALL_SPPED, settings.MAX_BALL_SPEED)

    def to_payload(self) -> WsBall:
        return WsBall(position=self.position)
