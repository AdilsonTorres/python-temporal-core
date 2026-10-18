"""uv run python -m exemplos.e10_automacao_rede.iniciar [--falhar-verificacao]"""

import sys
import time

from exemplos.comum import conectar, rodar

from .modelos import EventoRede
from .worker import TASK_QUEUE
from .workflows import RenomearDispositivoWorkflow


async def main(falhar: bool) -> None:
    client = await conectar()
    evento = EventoRede(
        evento_id=f"nb-{int(time.time() * 1000)}",
        dispositivo="sw-01",
        novo_nome="sw-core-01",
        falhar_verificacao=falhar,
    )
    handle = await client.start_workflow(
        RenomearDispositivoWorkflow.run,
        evento,
        id=f"rede-{evento.evento_id}",
        task_queue=TASK_QUEUE,
    )
    print(f"🚀 iniciado: {handle.id} (UI: http://localhost:8233)")
    print(f"🎉 resultado: {await handle.result()}")


if __name__ == "__main__":
    rodar(main("--falhar-verificacao" in sys.argv))
