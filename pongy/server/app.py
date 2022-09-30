import json
import logging

from aiohttp import web
from aiohttp import WSMsgType
from pydantic.error_wrappers import ValidationError

from pongy.models import WsCommand
from pongy.models import WsCookie
from pongy.models import WsErrorEvent
from pongy.models import WsErrorEventPayload
from pongy.models import WsEvent
from pongy.server.game import GamePool
from pongy.server.game import Player

logger = logging.getLogger(__name__)


class WebsocketHandler(web.View):
    async def get(self) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        try:
            cookie = WsCookie(**self.request.cookies)
            player = Player(uuid=cookie.player_id, ws=ws)
            async with GamePool(player):
                async for message in ws:
                    if message.type == WSMsgType.TEXT:
                        command = WsCommand(**json.loads(message.data))
                        player.move_racket(command.payload.direction)
        except Exception as err:  # pylint: disable=broad-except
            await self.send_error(err, ws)
            return ws
        else:
            logger.debug("Websocket connection closed")
            return ws

    @staticmethod
    async def send_error(error: Exception, ws: web.WebSocketResponse) -> None:
        if isinstance(error, ValidationError):
            message = str(
                ";".join(" ".join(map(str, e.values())) for e in error.errors())
            )
        else:
            message = str(error)
        logger.warning(message)
        await ws.send_json(
            WsEvent(
                data=WsErrorEvent(payload=WsErrorEventPayload(message=message))
            ).dict()
        )


class IndexHandler(web.View):
    async def get(self) -> web.Response:
        return web.json_response({})


def get_application() -> web.Application:
    app = web.Application()
    app.router.add_route("GET", "/", IndexHandler)
    app.router.add_route("GET", "/ws", WebsocketHandler)
    return app
