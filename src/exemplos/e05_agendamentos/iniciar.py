"""Cria um lembrete que dispara em N segundos (padrão: 20).

    uv run python -m exemplos.e05_agendamentos.iniciar [segundos]

Em outro terminal: temporal workflow signal --workflow-id lembrete-ana --name concluir
"""

import sys
from datetime import timedelta

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import Lembrete, LembreteWorkflow


async def main(segundos: int) -> None:
    client = await conectar()
    lembrete = Lembrete(usuario="ana", mensagem="hora da palestra!", em=timedelta(seconds=segundos))
    handle = await client.start_workflow(
        LembreteWorkflow.run, lembrete, id="lembrete-ana", task_queue=TASK_QUEUE
    )
    print(f"⏳ lembrete em {segundos}s ({handle.id})")
    print(f"🔔 {await handle.result()}")


if __name__ == "__main__":
    rodar(main(int(sys.argv[1]) if len(sys.argv) > 1 else 20))
