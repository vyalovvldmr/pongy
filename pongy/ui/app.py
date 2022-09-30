import asyncio
import logging
import queue
import threading
import uuid
from typing import Protocol

import aiohttp
import pygame

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import WsCommand
from pongy.models import WsCommandMovePayload
from pongy.models import WsErrorEvent
from pongy.models import WsEvent
from pongy.models import WsGameStateEvent
from pongy.ui.widgets.ball import BallWidget
from pongy.ui.widgets.racket import BottomRacketWidget
from pongy.ui.widgets.racket import LeftRacketWidget
from pongy.ui.widgets.racket import RightRacketWidget
from pongy.ui.widgets.racket import TopRacketWidget
from pongy.ui.widgets.score import BottomScoreWidget
from pongy.ui.widgets.score import LeftScoreWidget
from pongy.ui.widgets.score import RightScoreWidget
from pongy.ui.widgets.score import TopScoreWidget

logger = logging.getLogger(__name__)


class Exit:
    pass


class IApplication(Protocol):
    host: str
    port: int
    input_queue: queue.Queue[Exit | WsEvent]
    output_queue: queue.Queue[WsCommand]


class Connection(threading.Thread):
    def __init__(self, app: IApplication):
        super().__init__(daemon=True)
        self._app = app

    def run(self) -> None:
        self._connect()

    def connect(self) -> None:
        self.start()

    async def _process_output_queue(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        while True:
            await asyncio.sleep(1 / (settings.FPS * 10))
            while not self._app.output_queue.empty():
                await ws.send_json(self._app.output_queue.get_nowait().dict())

    async def _handle(self) -> None:
        player_id: str = str(uuid.uuid4())
        url = f"ws://{self._app.host}:{self._app.port}/ws"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    url,
                    heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                    headers={"Cookie": f"player_id={player_id}"},
                ) as ws:
                    asyncio.ensure_future(self._process_output_queue(ws))
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            ws_event = WsEvent.parse_raw(msg.data)
                            self._app.input_queue.put(ws_event)
        except aiohttp.ClientConnectionError:
            logger.error("Connection error")
            self._app.input_queue.put(Exit())

    def _connect(self) -> None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._handle())


class Application:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.input_queue: queue.Queue[Exit | WsEvent] = queue.Queue()
        self.output_queue: queue.Queue[WsCommand] = queue.Queue()

    def run(self) -> None:
        self._connect()
        pygame.init()
        surface = pygame.display.set_mode((settings.BOARD_SIZE, settings.BOARD_SIZE))
        surface.fill(settings.BOARD_COLOR)
        while True:
            ws_event = self.input_queue.get(block=True)
            if isinstance(ws_event, Exit):
                logger.info("Exit")
                break
            if isinstance(ws_event.data, WsErrorEvent):
                logger.error(ws_event.data.payload.message)
                break
            self._process_key_pressed()
            self._redraw(surface, ws_event.data)
        pygame.quit()

    def _connect(self) -> None:
        connection = Connection(app=self)
        connection.connect()

    def _redraw(
        self, surface: pygame.surface.Surface, ws_event: WsGameStateEvent
    ) -> None:
        surface.fill(settings.BOARD_COLOR)
        for player, racket_widget, score_widget in zip(
            ws_event.payload.players,
            (BottomRacketWidget, TopRacketWidget, LeftRacketWidget, RightRacketWidget),
            (BottomScoreWidget, TopScoreWidget, LeftScoreWidget, RightScoreWidget),
        ):
            racket_widget(player.racket_position).draw(surface)
            score_widget(player.score).draw(surface)

        ball_position = ws_event.payload.ball_position
        BallWidget(ball_position).draw(surface)
        pygame.display.flip()

    def _process_key_pressed(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.input_queue.put(Exit())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.input_queue.put(Exit())
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.LEFT)
            )
            self.output_queue.put(ws_event)
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.RIGHT)
            )
            self.output_queue.put(ws_event)
