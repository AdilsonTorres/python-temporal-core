"""uv run python -m exemplos.e09_benchmark_python.worker

max_concurrent_activities=1: benchmarks em paralelo brigam por CPU e estragam os números.
"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from . import activities as a
from .workflows import BenchmarkPythonWorkflow

TASK_QUEUE = "benchmark-python"
ACTIVITIES = [a.garantir_python, a.rodar_benchmark]


async def main() -> None:
    worker = Worker(
        await conectar(),
        task_queue=TASK_QUEUE,
        workflows=[BenchmarkPythonWorkflow],
        activities=ACTIVITIES,
        max_concurrent_activities=1,
    )
    print("⏳ worker de benchmark rodando (1 activity por vez)")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
