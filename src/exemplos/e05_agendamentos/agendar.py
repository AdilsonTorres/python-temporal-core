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

# Outras formas de dizer "quando" no ScheduleSpec (use uma ou combine):
#   cron_expressions=["0 9 * * MON-FRI"]                      # cron clássico
#   intervals=[ScheduleIntervalSpec(every=timedelta(hours=6), offset=timedelta(minutes=15))]
#                                                             # a cada 6h, às :15
#   calendars=[ScheduleCalendarSpec(hour=[ScheduleRange(9)], minute=[ScheduleRange(0)],
#                                   day_of_week=[ScheduleRange(1, 5)])]   # seg-sex, 09:00
#   time_zone_name="America/Sao_Paulo"                        # sem isso, vale UTC
#   jitter=timedelta(minutes=1)                               # atraso aleatório até 1 min
# E o que fazer quando uma execução demora ou o servidor ficou fora do ar:
#   policy=SchedulePolicy(
#       overlap=ScheduleOverlapPolicy.SKIP,   # ainda rodando? pula (ou BUFFER_ONE, ALLOW_ALL...)
#       catchup_window=timedelta(hours=1),    # recupera disparos perdidos até 1h atrás
#   )

schedule = Schedule(
    action=ScheduleActionStartWorkflow(
        RelatorioDiarioWorkflow.run, id="relatorio-diario", task_queue=TASK_QUEUE
    ),
    # Seg a sex, 08:00 (horário de São Paulo).
    spec=ScheduleSpec(cron_expressions=["0 8 * * 1-5"], time_zone_name="America/Sao_Paulo"),
    # policy=SchedulePolicy(...),  # veja as opções acima
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
