import pygame

from pongy import settings


class BaseRacket:
    def __init__(self, position):
        self._position = position

    def draw(self, surface):
        pass


class HorizontalRacket(BaseRacket):
    def __init__(self, position):
        super().__init__(position)
        self._width = settings.RACKET_LENGTH
        self._height = settings.RACKET_HEIGHT


class VerticalRacket(BaseRacket):
    def __init__(self, position):
        super().__init__(position)
        self._width = settings.RACKET_HEIGHT
        self._height = settings.RACKET_LENGTH


class FirstRacket(HorizontalRacket):
    def draw(self, surface):
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                self._position,
                0,
                self._width,
                self._height,
            ),
        )


class SecondRacket(VerticalRacket):
    def draw(self, surface):
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                0,
                self._position,
                self._width,
                self._height,
            ),
        )


class ThirdRacket(VerticalRacket):
    def draw(self, surface):
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                settings.BOARD_SIZE[0] - settings.RACKET_HEIGHT,
                self._position,
                self._width,
                self._height,
            ),
        )


class MyRacket(HorizontalRacket):
    def draw(self, surface):
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                self._position,
                settings.BOARD_SIZE[0] - settings.RACKET_HEIGHT,
                self._width,
                self._height,
            ),
        )
