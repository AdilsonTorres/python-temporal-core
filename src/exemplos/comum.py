"""Conexão com o Temporal compartilhada pelos exemplos."""

import asyncio
import os
from contextlib import suppress

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "127.0.0.1:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")


async def conectar() -> Client:
    # O conversor Pydantic permite usar modelos tipados como entrada e saída.
    return await Client.connect(
        TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE, data_converter=pydantic_data_converter
    )


def rodar(coro) -> None:
    # asyncio.run sem traceback quando o usuário aperta Ctrl+C.
    with suppress(KeyboardInterrupt):
        asyncio.run(coro)
