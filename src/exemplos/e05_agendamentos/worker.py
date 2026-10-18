"""uv run python -m exemplos.e05_agendamentos.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .workflows import (
    BoasVindasWorkflow,
    LembreteWorkflow,
    RelatorioDiarioWorkflow,
    enviar_mensagem,
    gerar_relatorio_diario,
)

TASK_QUEUE = "agendamentos"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[LembreteWorkflow, BoasVindasWorkflow, RelatorioDiarioWorkflow],
        activities=[enviar_mensagem, gerar_relatorio_diario],
    )
    print("👷 worker de agendamentos")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
