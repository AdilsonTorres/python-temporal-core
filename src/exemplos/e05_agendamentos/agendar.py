"""Cria (ou atualiza) um Schedule, o substituto do crontab.

uv run python -m exemplos.e05_agendamentos.agendar
"""

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleSpec,
    ScheduleUpdate,
    ScheduleUpdateInput,
)

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import RelatorioDiarioWorkflow

SCHEDULE_ID = "relatorio-diario"

schedule = Schedule(
    action=ScheduleActionStartWorkflow(
        RelatorioDiarioWorkflow.run, id="relatorio-diario", task_queue=TASK_QUEUE
    ),
    # Seg a sex, 08:00 (horário de São Paulo).
    spec=ScheduleSpec(cron_expressions=["0 8 * * 1-5"], time_zone_name="America/Sao_Paulo"),
)


def substituir(entrada: ScheduleUpdateInput) -> ScheduleUpdate:
    return ScheduleUpdate(schedule=schedule)


async def main() -> None:
    client = await conectar()
    try:
        await client.create_schedule(SCHEDULE_ID, schedule)
        print(f"📅 schedule '{SCHEDULE_ID}' criado")
    except ScheduleAlreadyRunningError:
        await client.get_schedule_handle(SCHEDULE_ID).update(substituir)
        print(f"📅 schedule '{SCHEDULE_ID}' atualizado")

    # Dispara agora, sem esperar as 08:00.
    await client.get_schedule_handle(SCHEDULE_ID).trigger()
    print("▶️ disparado uma vez: veja a aba Schedules na UI")


if __name__ == "__main__":
    rodar(main())
