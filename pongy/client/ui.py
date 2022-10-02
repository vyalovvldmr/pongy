import pygame

from pongy import settings
from pongy import version
from pongy.client.widgets.ball import BallWidget
from pongy.client.widgets.racket import RacketWidgetFactory
from pongy.client.widgets.score import ScoreWidgetFactory
from pongy.models import WsGameStateEvent


class Ui:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(f"Pongy v{version}")
        self._surface = pygame.display.set_mode(
            (settings.BOARD_SIZE, settings.BOARD_SIZE)
        )
        self._surface.fill(settings.BOARD_COLOR)

    @staticmethod
    def stop() -> None:
        pygame.quit()

    def redraw(self, ws_event: WsGameStateEvent) -> None:
        self._surface.fill(settings.BOARD_COLOR)
        for player in ws_event.payload.players:
            racket_widget = RacketWidgetFactory(player.racket.side).create(
                player.racket.position
            )
            score_widget = ScoreWidgetFactory(player.racket.side).create(player.score)
            racket_widget.draw(self._surface)
            score_widget.draw(self._surface)

        ball_widget = BallWidget(ws_event.payload.ball.position)
        ball_widget.draw(self._surface)
        pygame.display.flip()
