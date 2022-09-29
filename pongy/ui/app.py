import asyncio
import logging
import queue
import threading
import time
import uuid
from contextlib import suppress

import aiohttp
import pygame

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import WsCommand
from pongy.models import WsCommandMovePayload
from pongy.models import WsEvent
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


async def _process_output_queue(ws, output_queue):
    while True:
        await asyncio.sleep(0.01)
        with suppress(queue.Empty):
            await ws.send_json(output_queue.get_nowait().dict())


async def _handle(input_queue, output_queue, host, port):
    player_id: str = str(uuid.uuid4())
    url = f"ws://{host}:{port}/ws"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                url,
                heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                headers={"Cookie": f"player_id={player_id}"},
            ) as ws:
                asyncio.ensure_future(_process_output_queue(ws, output_queue))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        ws_event = WsEvent.parse_raw(msg.data)
                        input_queue.put(ws_event)
    except aiohttp.ClientConnectionError:
        logger.error("Connection error")
        input_queue.put(Exit())


def ws_connection(input_queue, output_queue, host, port):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_handle(input_queue, output_queue, host, port))


class Application:
    def __init__(self, host: str, port: int):
        self._quit: bool = False
        self._host: str = host
        self._port: int = port
        self._input_queue: queue.Queue = queue.Queue()
        self._output_queue: queue.Queue = queue.Queue()

    def connect(self):
        keep_connection = threading.Thread(
            target=ws_connection,
            args=(self._input_queue, self._output_queue, self._host, self._port),
            daemon=True,
        )
        keep_connection.start()

    def draw_field(self, surface, ws_event):
        surface.fill(settings.BOARD_COLOR)
        for player, racket_widget, score_widget in zip(
            ws_event.data.payload.players,
            (BottomRacketWidget, TopRacketWidget, LeftRacketWidget, RightRacketWidget),
            (BottomScoreWidget, TopScoreWidget, LeftScoreWidget, RightScoreWidget),
        ):
            racket_widget(player.racket_position).draw(surface)
            score_widget(player.score).draw(surface)

        ball_position = ws_event.data.payload.ball_position
        BallWidget(ball_position).draw(surface)
        pygame.display.flip()

    def process_pygame_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self._quit = True

    def process_key_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.LEFT)
            )
            self._output_queue.put(ws_event)
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.RIGHT)
            )
            self._output_queue.put(ws_event)

    def process_input_queue(self, surface):
        while not self._input_queue.empty():
            ws_event = self._input_queue.get_nowait()
            if isinstance(ws_event, Exit):
                self._quit = True
                break
            self.draw_field(surface, ws_event)

    def run(self):
        self.connect()
        pygame.init()
        surface = pygame.display.set_mode((settings.BOARD_SIZE, settings.BOARD_SIZE))
        surface.fill(settings.BOARD_COLOR)
        while not self._quit:
            time.sleep(0.01)
            self.process_input_queue(surface)
            self.process_pygame_events()
            self.process_key_pressed()
        pygame.quit()
