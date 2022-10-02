import asyncio
import logging
import threading
from typing import Any

import aiohttp

from pongy import settings
from pongy.models import WsEvent
from pongy.ui import ExitEvent
from pongy.ui import IApplication

logger = logging.getLogger(__name__)


class WebsocketConnection(threading.Thread):
    def __init__(self, app: IApplication):
        super().__init__(daemon=True)
        self._app = app
        self._headers: dict[str, str] = {}
        self._host: str = settings.SERVER_HOST
        self._port: int = settings.SERVER_PORT

    def run(self) -> None:
        self._connect()

    def connect(
        self,
        host: str = settings.SERVER_HOST,
        port: int = settings.SERVER_PORT,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._headers = headers or {}
        self.start()

    async def _keep_connection(self) -> None:
        url = f"ws://{self._host}:{self._port}/ws"
        process_command_queue_task: asyncio.Task[Any] | None = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    url,
                    heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                    headers=self._headers,
                ) as ws:
                    process_command_queue_task = asyncio.create_task(
                        self._process_command_queue(ws)
                    )
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            ws_event = WsEvent.parse_raw(msg.data)
                            self._app.event_queue.put(ws_event)
        except aiohttp.ClientConnectionError:
            logger.error("Connection error")
        except Exception as err:  # pylint: disable=broad-except
            logger.exception(err)
        else:
            logger.error("Connection lost")
        finally:
            self._app.event_queue.put(ExitEvent())
            if process_command_queue_task:
                process_command_queue_task.cancel()

    def _connect(self) -> None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._keep_connection())

    async def _process_command_queue(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        while True:
            await asyncio.sleep(1 / (settings.FPS * 10))
            while not self._app.command_queue.empty():
                await ws.send_json(self._app.command_queue.get_nowait().dict())
