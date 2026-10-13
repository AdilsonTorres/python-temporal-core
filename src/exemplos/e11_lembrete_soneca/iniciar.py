"""Cria um lembrete curto e manda sonecas/confirmação.

uv run python -m exemplos.e11_lembrete_soneca.iniciar
Manual: signal `adiar` / `dispensar` pela UI ou `temporal workflow signal`.
"""

import asyncio
import time

from exemplos.comum import conectar, rodar

from .modelos import Lembrete
from .worker import TASK_QUEUE
from .workflows import LembreteWorkflow


async def main() -> None:
    client = await conectar()
    lembrete = Lembrete(texto="tomar água 💧", atraso_s=2, soneca_s=1, max_sonecas_por_execucao=2)
    handle = await client.start_workflow(
        LembreteWorkflow.run, lembrete, id=f"lembrete-{int(time.time())}", task_queue=TASK_QUEUE
    )
    print(f"🚀 iniciado: {handle.id} (UI: http://localhost:8233)")
    for _ in range(3):  # soneca 3x: força um continue_as_new
        await asyncio.sleep(2.5)
        print(f"📋 {await handle.query(LembreteWorkflow.status)} -> adiar")
        await handle.signal(LembreteWorkflow.adiar)
    await asyncio.sleep(1.5)
    await handle.signal(LembreteWorkflow.dispensar)
    print(f"🎉 resultado: {await handle.result()}")


if __name__ == "__main__":
    rodar(main())
