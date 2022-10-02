import logging
import uuid

import pygame

from pongy import settings
from pongy import version
from pongy.client.api import Api
from pongy.client.connection import ExitEvent
from pongy.client.widgets.ball import BallWidget
from pongy.client.widgets.racket import RacketWidgetFactory
from pongy.client.widgets.score import ScoreWidgetFactory
from pongy.models import MoveDirection
from pongy.models import WsErrorEvent
from pongy.models import WsGameStateEvent

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, host: str, port: int):
        player_id: str = str(uuid.uuid4())
        self._api = Api(
            host=host,
            port=port,
            headers={"Cookie": f"player_id={player_id}"},
        )

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption(f"Pongy v{version}")
        surface = pygame.display.set_mode((settings.BOARD_SIZE, settings.BOARD_SIZE))
        surface.fill(settings.BOARD_COLOR)
        while True:
            event = self._api.get_event_blocking()
            if isinstance(event, ExitEvent):
                logger.info("Exit")
                break
            if isinstance(event.data, WsErrorEvent):
                logger.error(event.data.payload.message)
                break
            self._process_key_pressed()
            self._redraw(surface, event.data)
        pygame.quit()

    def _redraw(
        self, surface: pygame.surface.Surface, ws_event: WsGameStateEvent
    ) -> None:
        surface.fill(settings.BOARD_COLOR)
        for player in ws_event.payload.players:
            racket_widget = RacketWidgetFactory(player.racket.side).create(
                player.racket.position
            )
            score_widget = ScoreWidgetFactory(player.racket.side).create(player.score)
            racket_widget.draw(surface)
            score_widget.draw(surface)

        ball_widget = BallWidget(ws_event.payload.ball.position)
        ball_widget.draw(surface)
        pygame.display.flip()

    def _process_key_pressed(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.debug("Got exit signal")
                self._api.notify(ExitEvent())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    logger.debug("Got exit signal")
                    self._api.notify(ExitEvent())
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            self._api.move(direction=MoveDirection.LEFT)
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            self._api.move(direction=MoveDirection.RIGHT)
