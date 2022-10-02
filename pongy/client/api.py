import asyncio
import queue

import aiohttp

from pongy import settings
from pongy.client.connection import ExitEvent
from pongy.client.connection import WebsocketConnection
from pongy.models import MoveDirection
from pongy.models import WsCommand
from pongy.models import WsCommandMovePayload
from pongy.models import WsEvent


class Api:
    def __init__(
        self,
        host: str = settings.SERVER_HOST,
        port: int = settings.SERVER_PORT,
        headers: dict[str, str] | None = None,
    ):
        self._event_queue: queue.Queue[WsEvent | ExitEvent] = queue.Queue()
        self._command_queue: queue.Queue[WsCommand] = queue.Queue()
        connection = WebsocketConnection(
            headers=headers, host=host, port=port, api=self
        )
        connection.connect()

    async def publish_commands(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        while True:
            await asyncio.sleep(1 / (settings.FPS * 10))
            while not self._command_queue.empty():
                await ws.send_json(self._command_queue.get_nowait().dict())

    def notify(self, ws_event: WsEvent | ExitEvent) -> None:
        self._event_queue.put(ws_event)

    def move(self, direction: MoveDirection) -> None:
        ws_event = WsCommand(payload=WsCommandMovePayload(direction=direction))
        self._command_queue.put(ws_event)

    def get_event_blocking(self) -> ExitEvent | WsEvent:
        return self._event_queue.get(block=True)
