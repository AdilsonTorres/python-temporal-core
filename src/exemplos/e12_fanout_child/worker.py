"""uv run python -m exemplos.e12_fanout_child.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import gerar_relatorio
from .workflows import RelatoriosWorkflow, RelatorioWorkflow

TASK_QUEUE = "fanout"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[RelatoriosWorkflow, RelatorioWorkflow],
        activities=[gerar_relatorio],
    )
    print("👷 worker de relatórios")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
