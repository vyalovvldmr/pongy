import logging
import uuid

from pongy.client.connection import ExitEvent
from pongy.client.connection import WebsocketConnection
from pongy.client.controls import KeyboardControls
from pongy.client.ui import Ui
from pongy.models import WsErrorEvent

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, host: str, port: int):
        player_id: str = str(uuid.uuid4())
        self.ui = Ui()
        self.controls = KeyboardControls()
        self.connection = WebsocketConnection(
            host=host, port=port, headers={"Cookie": f"player_id={player_id}"}
        )

    async def run(self) -> None:
        async with self.connection as connection:
            while True:
                event = await connection.get_event_blocking()
                if self.controls.is_exit_pressed() or isinstance(event, ExitEvent):
                    logger.debug("Exit")
                    break
                if isinstance(event.data, WsErrorEvent):
                    logger.error(event.data.payload.message)
                    break
                action = self.controls.get_action()
                if action:
                    await connection.send_action(action)
                self.ui.redraw(event.data)
        self.ui.stop()
