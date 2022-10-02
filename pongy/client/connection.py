import asyncio
import logging
from contextlib import suppress
from typing import Any

import aiohttp

from pongy import settings
from pongy.models import MoveDirection
from pongy.models import WsCommand
from pongy.models import WsCommandMovePayload
from pongy.models import WsEvent

logger = logging.getLogger(__name__)


class ExitEvent:
    pass


class WebsocketConnection:
    def __init__(
        self,
        host: str = settings.SERVER_HOST,
        port: int = settings.SERVER_PORT,
        headers: dict[str, str] | None = None,
    ):
        self._headers: dict[str, str] = headers or {}
        self._host: str = host
        self._port: int = port
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._event_queue: asyncio.Queue[WsEvent | ExitEvent] = asyncio.Queue()
        self._background_task: asyncio.Task[Any] | None = None

    async def __aenter__(self) -> "WebsocketConnection":
        self._background_task = asyncio.create_task(self._keep_connection())
        return self

    async def __aexit__(self, *args: tuple[Any, ...]) -> None:
        if self._background_task:
            self._background_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._background_task

    async def send_action(self, direction: MoveDirection) -> None:
        if self._ws:
            ws_event = WsCommand(payload=WsCommandMovePayload(direction=direction))
            await self._ws.send_json(ws_event.dict())

    async def get_event_blocking(self) -> ExitEvent | WsEvent:
        return await self._event_queue.get()

    async def _keep_connection(self) -> None:
        url = f"ws://{self._host}:{self._port}/ws"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    url,
                    heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                    headers=self._headers,
                ) as ws:
                    self._ws = ws
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            ws_event = WsEvent.parse_raw(msg.data)
                            self._event_queue.put_nowait(ws_event)
        except aiohttp.ClientConnectionError:
            logger.error("Connection error")
        except Exception as err:  # pylint: disable=broad-except
            logger.exception(err)
        else:
            logger.error("Connection lost")
        finally:
            self._event_queue.put_nowait(ExitEvent())
