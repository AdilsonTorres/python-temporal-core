"""uv run python -m exemplos.e06_agente.worker"""

from pydantic_ai.durable_exec.temporal import PydanticAIPlugin
from temporalio.client import Client
from temporalio.worker import Worker

from exemplos.comum import TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, rodar

from .workflows import AgenteMcpWorkflow, AgenteOpsWorkflow

TASK_QUEUE = "agentes"


async def conectar_agentes() -> Client:
    # O plugin configura o conversor de dados e o sandbox para o Pydantic AI
    return await Client.connect(
        TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE, plugins=[PydanticAIPlugin()]
    )


async def main() -> None:
    client = await conectar_agentes()
    worker = Worker(client, task_queue=TASK_QUEUE, workflows=[AgenteOpsWorkflow, AgenteMcpWorkflow])
    print("🤖 worker de agentes rodando")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
