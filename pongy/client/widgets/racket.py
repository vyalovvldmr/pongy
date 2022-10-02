import pygame

from pongy import settings
from pongy.models import BoardSide


class BaseRacketWidget:
    def __init__(self, position: int):
        self._position = position

    def draw(self, surface: pygame.surface.Surface) -> None:
        pass


class HorizontalRacketWidget(BaseRacketWidget):
    def __init__(self, position: int):
        super().__init__(position)
        self._width = settings.RACKET_LENGTH
        self._height = settings.RACKET_HEIGHT


class VerticalRacketWidget(BaseRacketWidget):
    def __init__(self, position: int):
        super().__init__(position)
        self._width = settings.RACKET_HEIGHT
        self._height = settings.RACKET_LENGTH


class TopRacketWidget(HorizontalRacketWidget):
    def draw(self, surface: pygame.surface.Surface) -> None:
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


class LeftRacketWidget(VerticalRacketWidget):
    def draw(self, surface: pygame.surface.Surface) -> None:
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


class RightRacketWidget(VerticalRacketWidget):
    def draw(self, surface: pygame.surface.Surface) -> None:
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                settings.BOARD_SIZE - settings.RACKET_HEIGHT,
                self._position,
                self._width,
                self._height,
            ),
        )


class BottomRacketWidget(HorizontalRacketWidget):
    def draw(self, surface: pygame.surface.Surface) -> None:
        pygame.draw.rect(
            surface,
            settings.RACKET_COLOR,
            pygame.Rect(
                self._position,
                settings.BOARD_SIZE - settings.RACKET_HEIGHT,
                self._width,
                self._height,
            ),
        )


class RacketWidgetFactory:
    def __init__(self, side: BoardSide):
        self.side = side

    def create(self, position: int) -> BaseRacketWidget:
        mapping = {
            BoardSide.RIGHT: RightRacketWidget,
            BoardSide.LEFT: LeftRacketWidget,
            BoardSide.TOP: TopRacketWidget,
            BoardSide.BOTTOM: BottomRacketWidget,
        }
        return mapping[self.side](position)
