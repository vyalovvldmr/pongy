import pygame

from pongy import settings


class Ball:
    def __init__(self, position):
        self._position = position
        self._width = 10
        self._height = 10

    def draw(self, surface):
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
