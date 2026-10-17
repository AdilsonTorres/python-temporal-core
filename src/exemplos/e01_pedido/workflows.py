"""Workflow: o caminho feliz em Python comum; o Temporal cuida de falhas e retries."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import cobrar, enviar, notificar_cliente, reservar_estoque, validar_pedido
    from .modelos import Pedido, ResultadoPedido

TIMEOUT = timedelta(seconds=10)  # curto: após um kill -9, o passo volta em até 10s
RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    non_retryable_error_types=["ValueError"],  # erro de negócio: não repete
)


@workflow.defn
class PedidoWorkflow:
    def __init__(self) -> None:
        self.passo = "iniciado"

    @workflow.run
    async def run(self, pedido: Pedido) -> ResultadoPedido:
        self.passo = "validando"
        await workflow.execute_activity(
            validar_pedido, pedido, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )

        self.passo = "cobrando"
        pagamento_id = await workflow.execute_activity(
            cobrar, pedido, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )

        self.passo = "reservando"
        await workflow.execute_activity(
            reservar_estoque, pedido, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )

        self.passo = "enviando"
        rastreio = await workflow.execute_activity(
            enviar, pedido, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )

        self.passo = "notificando"
        await workflow.execute_activity(
            notificar_cliente,
            args=[pedido, rastreio],
            start_to_close_timeout=TIMEOUT,
            retry_policy=RETRY,
        )

        self.passo = "concluído"
        return ResultadoPedido(pedido_id=pedido.id, pagamento_id=pagamento_id, rastreio=rastreio)

    @workflow.query
    def status(self) -> str:
        return self.passo
