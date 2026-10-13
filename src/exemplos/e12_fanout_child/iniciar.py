"""Gera 10 relatórios em lotes de 3 e acompanha o progresso pela Query.

uv run python -m exemplos.e12_fanout_child.iniciar
"""

import asyncio
import time

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import RelatoriosWorkflow


async def main() -> None:
    client = await conectar()
    handle = await client.start_workflow(
        RelatoriosWorkflow.run,
        args=[10, 3],
        id=f"relatorios-{int(time.time())}",
        task_queue=TASK_QUEUE,
    )
    print(f"🚀 iniciado: {handle.id} (UI: http://localhost:8233)")
    resultado = asyncio.ensure_future(handle.result())
    while not resultado.done():
        print(f"📊 progresso: {await handle.query(RelatoriosWorkflow.progresso)}")
        await asyncio.wait([resultado], timeout=1)
    print(f"🎉 concluído: {len(resultado.result())} arquivos")


if __name__ == "__main__":
    rodar(main())
