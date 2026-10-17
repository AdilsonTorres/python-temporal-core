"""Servidor Temporal local (gRPC :7233, UI http://localhost:8233).

uv run python -m exemplos.servidor_dev
"""

import asyncio
import signal

from temporalio.testing import WorkflowEnvironment

from exemplos.comum import rodar


async def main() -> None:
    env = await WorkflowEnvironment.start_local(
        port=7233, ui=True, ui_port=8233, dev_server_database_filename="temporal-dev.db"
    )
    parar = asyncio.Event()
    # kill/SIGTERM também desliga o servidor (não deixa processo órfão)
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, parar.set)
    async with env:
        print("Temporal rodando em 127.0.0.1:7233 | UI: http://localhost:8233 (Ctrl+C sai)")
        await parar.wait()


if __name__ == "__main__":
    rodar(main())
