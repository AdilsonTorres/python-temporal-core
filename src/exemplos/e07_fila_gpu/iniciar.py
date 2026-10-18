"""uv run python -m exemplos.e07_fila_gpu.iniciar [N]"""

import sys
import time

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import InferenciaWorkflow


async def main(n: int) -> None:
    client = await conectar()
    lote = int(time.time())

    handles = []
    for i in range(1, n + 1):
        handle = await client.start_workflow(
            InferenciaWorkflow.run,
            f"pergunta {i}",
            id=f"inferencia-{lote}-{i}",
            task_queue=TASK_QUEUE,
        )
        handles.append(handle)
    print(f"⏳ {n} prompts na fila")

    for handle in handles:
        print(f"✅ {handle.id}: {await handle.result()}")


if __name__ == "__main__":
    rodar(main(int(sys.argv[1]) if len(sys.argv) > 1 else 5))
