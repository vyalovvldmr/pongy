import logging
import queue
import uuid

import pygame

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import WsCommand
from pongy.models import WsCommandMovePayload
from pongy.models import WsErrorEvent
from pongy.models import WsEvent
from pongy.models import WsGameStateEvent
from pongy.ui import ExitEvent
from pongy.ui.connection import WebsocketConnection
from pongy.ui.widgets.ball import BallWidget
from pongy.ui.widgets.racket import RacketWidgetFactory
from pongy.ui.widgets.score import ScoreWidgetFactory

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, host: str, port: int):
        self.event_queue: queue.Queue[WsEvent | ExitEvent] = queue.Queue()
        self.command_queue: queue.Queue[WsCommand] = queue.Queue()
        self._host: str = host
        self._port: int = port

    def run(self) -> None:
        player_id: str = str(uuid.uuid4())
        ws_connection = WebsocketConnection(app=self)
        ws_connection.connect(
            host=self._host,
            port=self._port,
            headers={"Cookie": f"player_id={player_id}"},
        )
        pygame.init()
        surface = pygame.display.set_mode((settings.BOARD_SIZE, settings.BOARD_SIZE))
        surface.fill(settings.BOARD_COLOR)
        while True:
            event = self.event_queue.get(block=True)
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

        ball_position = ws_event.payload.ball.position
        BallWidget(ball_position).draw(surface)
        pygame.display.flip()

    def _process_key_pressed(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.debug("Got exit signal")
                self.event_queue.put(ExitEvent())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    logger.debug("Got exit signal")
                    self.event_queue.put(ExitEvent())
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.LEFT)
            )
            self.command_queue.put(ws_event)
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.RIGHT)
            )
            self.command_queue.put(ws_event)
