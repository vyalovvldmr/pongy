import pygame

from pongy import settings


class BallWidget:
    def __init__(self, position: tuple[int, int]):
        self._position = position
        self._width = settings.BALL_SIZE
        self._height = settings.BALL_SIZE

    def draw(self, surface: pygame.surface.Surface) -> None:
        pygame.draw.rect(
            surface,
            settings.BALL_COLOR,
            pygame.Rect(
                self._position[0],
                self._position[1],
                self._width,
                self._height,
            ),
        )
