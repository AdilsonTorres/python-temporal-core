"""Abre um carrinho, mexe nele por Updates e fecha.

uv run python -m exemplos.e14_entidade_carrinho.iniciar
"""

import time

from temporalio.client import WorkflowUpdateFailedError

from exemplos.comum import conectar, rodar

from .modelos import Carrinho, Item
from .worker import TASK_QUEUE
from .workflows import CarrinhoWorkflow


async def main() -> None:
    client = await conectar()
    handle = await client.start_workflow(
        CarrinhoWorkflow.run,
        Carrinho(cliente="ana"),
        id=f"carrinho-ana-{int(time.time())}",
        task_queue=TASK_QUEUE,
    )
    print(f"🚀 carrinho aberto: {handle.id} (UI: http://localhost:8233)")
    cw = CarrinhoWorkflow
    total = await handle.execute_update(cw.adicionar, Item(sku="teclado", quantidade=1, preco=250))
    print(f"🛒 teclado: total {total}")
    total = await handle.execute_update(cw.adicionar, Item(sku="mouse", quantidade=2, preco=50))
    print(f"🛒 mouse x2: total {total}")
    try:
        await handle.execute_update(cw.adicionar, Item(sku="x", quantidade=0, preco=1))
    except WorkflowUpdateFailedError as erro:
        print(f"🚫 validador recusou: {erro.cause}")
    print(f"🧹 sem mouse: total {await handle.execute_update(cw.remover, 'mouse')}")
    print(f"📊 query total: {await handle.query(cw.total)}")
    await handle.execute_update(CarrinhoWorkflow.fechar)
    print(f"🎉 {await handle.result()}")


if __name__ == "__main__":
    rodar(main())
