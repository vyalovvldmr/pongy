import logging

import click
from pythonjsonlogger import jsonlogger

from pongy import settings


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-d", "--daemon", is_flag=True, help="Run server.")
@click.option(
    "-h",
    "--host",
    help="Hostname",
    type=click.STRING,
    default=settings.SERVER_HOST,
)
@click.option(
    "-p",
    "--port",
    help="Port",
    type=click.INT,
    default=settings.SERVER_PORT,
)
def main(daemon: bool, host: str, port: int) -> None:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(jsonlogger.JsonFormatter(timestamp=True))
    logging.basicConfig(level=settings.LOGGING_LEVEL, handlers=[stream_handler])
    if daemon:
        from aiohttp import web

        from pongy.server.app import get_application

        web.run_app(get_application(), host=host, port=port)
    else:
        from pongy.ui.app import Application

        app = Application(host, port)
        app.run()


if __name__ == "__main__":
    main()
