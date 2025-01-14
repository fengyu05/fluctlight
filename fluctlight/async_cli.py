# pylint: disable=C0415
# pylint: disable=unused-import
"""CLI entrypoint."""

import asyncclick as click

from fluctlight.logger import get_logger

logger = get_logger(__name__)


@click.group()
def main() -> None:
    pass


@main.command()
async def start() -> None:
    from fluctlight.server import start_server

    logger.debug("Debug log is on[if you see this]")
    start_server()


# Backdoor testing code block
@main.command()
async def backdoor() -> None:
    pass
