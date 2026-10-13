"""Roda o canário uma vez, ou o agenda a cada 30s.

uv run python -m exemplos.e13_canario_worker.iniciar [--agendar]
"""

import sys
import time
from datetime import timedelta

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import CanarioWorkflow

# "fantasma" não tem worker: o canário deve alertar.
FILAS = [TASK_QUEUE, "fantasma"]


async def main(agendar: bool) -> None:
    client = await conectar()
    if agendar:
        await client.create_schedule(
            "canario",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    CanarioWorkflow.run,
                    args=[FILAS, 60],
                    id="canario-agendado",
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(seconds=30))]),
            ),
        )
        print("📅 schedule `canario` criado (a cada 30s)")
        return
    resultado = await client.execute_workflow(
        CanarioWorkflow.run,
        args=[FILAS, 60],
        id=f"canario-{int(time.time())}",
        task_queue=TASK_QUEUE,
    )
    print(f"🎉 alertas: {resultado}")


if __name__ == "__main__":
    rodar(main("--agendar" in sys.argv))
