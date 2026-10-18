"""uv run python -m exemplos.e07_fila_gpu.worker

Demo: suba o backend_falso, rode `.iniciar 5`, mate o backend, suba de novo.
"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import gerar_resposta
from .workflows import InferenciaWorkflow

TASK_QUEUE = "fila-gpu"
MAX_INFERENCIAS_SIMULTANEAS = 1  # protege a VRAM: uma inferência por vez


def criar_worker(client) -> Worker:
    return Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[InferenciaWorkflow],
        activities=[gerar_resposta],
        max_concurrent_activities=MAX_INFERENCIAS_SIMULTANEAS,
    )


async def main() -> None:
    worker = criar_worker(await conectar())
    print("⏳ worker da fila de GPU rodando (1 inferência por vez)")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
