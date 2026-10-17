"""uv run python -m exemplos.e04_aprovacao.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .workflows import DeployComAprovacaoWorkflow, fazer_deploy

TASK_QUEUE = "aprovacoes"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DeployComAprovacaoWorkflow],
        activities=[fazer_deploy],
    )
    print("👷 worker de aprovações")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
