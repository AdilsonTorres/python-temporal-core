"""uv run python -m exemplos.e10_automacao_rede.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import aplicar_config, notificar, reverter_config, validar_no_inventario, verificar
from .workflows import RenomearDispositivoWorkflow

TASK_QUEUE = "rede"
ACTIVITIES = [validar_no_inventario, aplicar_config, verificar, reverter_config, notificar]


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[RenomearDispositivoWorkflow],
        activities=ACTIVITIES,
    )
    print("👷 worker de automação de rede")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
