from typing import Protocol

import pygame

from pongy import settings
from pongy.models import BoardSide


class IScoreWidget(Protocol):
    def draw(self, surface: pygame.surface.Surface) -> None:
        pass


class BaseScoreWidget:
    position = (0, 0)

    def __init__(self, score: int):
        self._score = str(score)

    def draw(self, surface: pygame.surface.Surface) -> None:
        font = pygame.font.Font(None, settings.SCORE_FONT_SIZE)
        text = font.render(self._score, True, settings.SCORE_FONT_COLOR)
        text_rect = text.get_rect(center=self.position)
        surface.blit(text, text_rect)


class BottomScoreWidget(BaseScoreWidget):
    position = (
        settings.BOARD_SIZE // 2,
        settings.BOARD_SIZE // 2 + settings.SCORE_TEXT_SHIFT,
    )


class TopScoreWidget(BaseScoreWidget):
    position = (
        settings.BOARD_SIZE // 2,
        settings.BOARD_SIZE // 2 - settings.SCORE_TEXT_SHIFT,
    )


class LeftScoreWidget(BaseScoreWidget):
    position = (
        settings.BOARD_SIZE // 2 - settings.SCORE_TEXT_SHIFT,
        settings.BOARD_SIZE // 2,
    )


class RightScoreWidget(BaseScoreWidget):
    position = (
        settings.BOARD_SIZE // 2 + settings.SCORE_TEXT_SHIFT,
        settings.BOARD_SIZE // 2,
    )


class ScoreWidgetFactory:
    def __init__(self, side: BoardSide):
        self.side = side

    def create(self, score: int) -> IScoreWidget:
        mapping = {
            BoardSide.RIGHT: RightScoreWidget,
            BoardSide.LEFT: LeftScoreWidget,
            BoardSide.TOP: TopScoreWidget,
            BoardSide.BOTTOM: BottomScoreWidget,
        }
        return mapping[self.side](score)
