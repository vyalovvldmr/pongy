import queue
from typing import Protocol

from pongy.models import WsCommand
from pongy.models import WsEvent


class ExitEvent:
    pass


class IApplication(Protocol):
    event_queue: queue.Queue[WsEvent | ExitEvent]
    command_queue: queue.Queue[WsCommand]
