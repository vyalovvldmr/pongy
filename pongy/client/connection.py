import asyncio
import logging
import threading
from typing import Any
from typing import Protocol

import aiohttp

from pongy import settings
from pongy.models import WsEvent

logger = logging.getLogger(__name__)


class ExitEvent:
    pass


class IApi(Protocol):
    async def publish_commands(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        pass

    def notify(self, ws_event: WsEvent | ExitEvent) -> None:
        pass


class WebsocketConnection(threading.Thread):
    def __init__(
        self,
        api: IApi,
        host: str = settings.SERVER_HOST,
        port: int = settings.SERVER_PORT,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(daemon=True)
        self._headers: dict[str, str] = headers or {}
        self._host: str = host
        self._port: int = port
        self._api: IApi = api

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._keep_connection())

    def connect(self) -> None:
        self.start()

    async def _keep_connection(self) -> None:
        url = f"ws://{self._host}:{self._port}/ws"
        publish_commands_task: asyncio.Task[Any] | None = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    url,
                    heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                    headers=self._headers,
                ) as ws:
                    publish_commands_task = asyncio.create_task(
                        self._api.publish_commands(ws)
                    )
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            ws_event = WsEvent.parse_raw(msg.data)
                            self._api.notify(ws_event)
        except aiohttp.ClientConnectionError:
            logger.error("Connection error")
        except Exception as err:  # pylint: disable=broad-except
            logger.exception(err)
        else:
            logger.error("Connection lost")
        finally:
            self._api.notify(ExitEvent())
            if publish_commands_task:
                publish_commands_task.cancel()
