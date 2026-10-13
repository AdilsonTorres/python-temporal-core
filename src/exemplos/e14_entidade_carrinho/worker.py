"""uv run python -m exemplos.e14_entidade_carrinho.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import registrar_pedido
from .workflows import CarrinhoWorkflow

TASK_QUEUE = "carrinho"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client, task_queue=TASK_QUEUE, workflows=[CarrinhoWorkflow], activities=[registrar_pedido]
    )
    print("👷 worker do carrinho")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
