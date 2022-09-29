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
from pongy.ui.ball import Ball
from pongy.ui.racket import BottomRacketWidget
from pongy.ui.racket import LeftRacketWidget
from pongy.ui.racket import RightRacketWidget
from pongy.ui.racket import TopRacketWidget
from pongy.ui.score import BottomScoreWidget
from pongy.ui.score import LeftScoreWidget
from pongy.ui.score import RightScoreWidget
from pongy.ui.score import TopScoreWidget

logger = logging.getLogger(__name__)


class Exit:
    pass


def run_app(host: str, port: int):
    pygame.init()
    quit = False
    input_queue: queue.Queue = queue.Queue()
    output_queue: queue.Queue = queue.Queue()
    player_id = str(uuid.uuid4())

    def ws_connection():
        async def _process_output_queue(ws):
            while True:
                await asyncio.sleep(0.01)
                with suppress(queue.Empty):
                    await ws.send_json(output_queue.get_nowait().dict())

        async def _handle():
            url = f"ws://{host}:{port}/ws"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        url,
                        heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                        headers={"Cookie": f"player_id={player_id}"},
                    ) as ws:
                        task = asyncio.ensure_future(_process_output_queue(ws))
                        async for msg in ws:
                            if quit or msg.type == aiohttp.WSMsgType.ERROR:
                                task.cancel()
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                ws_event = WsEvent.parse_raw(msg.data)
                                input_queue.put(ws_event)
            except aiohttp.ClientConnectionError:
                logger.error("Connection error")
                input_queue.put(Exit())

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_handle())

    keep_connection = threading.Thread(target=ws_connection)
    keep_connection.start()

    surface = pygame.display.set_mode((settings.BOARD_SIZE, settings.BOARD_SIZE))
    surface.fill(settings.BOARD_COLOR)

    while not quit:
        time.sleep(0.01)
        while not input_queue.empty():
            ws_event = input_queue.get_nowait()
            if isinstance(ws_event, Exit):
                quit = True
                break
            surface.fill(settings.BOARD_COLOR)
            for player, racket_widget, score_widget in zip(
                ws_event.data.payload.players,
                (
                    BottomRacketWidget,
                    TopRacketWidget,
                    LeftRacketWidget,
                    RightRacketWidget,
                ),
                (BottomScoreWidget, TopScoreWidget, LeftScoreWidget, RightScoreWidget),
            ):
                racket_widget(player.racket_position).draw(surface)
                score_widget(player.score).draw(surface)

            ball_position = ws_event.data.payload.ball_position
            Ball(ball_position).draw(surface)
            pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    quit = True
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.LEFT)
            )
            output_queue.put(ws_event)
        if keys[pygame.K_RIGHT]:
            ws_event = WsCommand(
                payload=WsCommandMovePayload(direction=MoveDirection.RIGHT)
            )
            output_queue.put(ws_event)
    pygame.quit()
