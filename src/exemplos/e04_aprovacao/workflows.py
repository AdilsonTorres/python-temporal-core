"""Human-in-the-loop: o workflow espera uma pessoa aprovar (ou 3 dias passarem).

Update `aprovar` (com validador), Signal `rejeitar`, Query `status`.
Update `registrar_pedido`: o cli inicia e recebe o estado numa chamada (Update-with-Start).
"""

from datetime import timedelta

from pydantic import BaseModel
from temporalio import activity, workflow


class PedidoDeploy(BaseModel):
    servico: str
    versao: str
    solicitante: str


class Aprovacao(BaseModel):
    aprovador: str


@activity.defn
async def fazer_deploy(pedido: PedidoDeploy) -> str:
    print(f"🚀 deploy de {pedido.servico} {pedido.versao}", flush=True)
    return f"{pedido.servico}@{pedido.versao} no ar"


@workflow.defn
class DeployComAprovacaoWorkflow:
    @workflow.init  # roda antes de qualquer Update: os handlers já veem o pedido
    def __init__(self, pedido: PedidoDeploy) -> None:
        self.estado = "aguardando aprovação"
        self.aprovador = ""
        self.rejeitado_por = ""
        self.solicitante = pedido.solicitante

    @workflow.run
    async def run(self, pedido: PedidoDeploy) -> str:
        resultado = await self._decidir(pedido)
        # Não encerra no meio de um Update/Signal em andamento.
        await workflow.wait_condition(workflow.all_handlers_finished)
        return resultado

    async def _decidir(self, pedido: PedidoDeploy) -> str:
        try:
            # Timer durável: sobrevive a deploys e reinícios do worker.
            await workflow.wait_condition(
                lambda: self.aprovador != "" or self.rejeitado_por != "",
                timeout=timedelta(days=3),
            )
        except TimeoutError:
            self.estado = "expirado"
            return "rejeitado: ninguém aprovou em 3 dias"

        if self.rejeitado_por:
            self.estado = "rejeitado"
            return f"rejeitado por {self.rejeitado_por}"

        self.estado = "em deploy"
        resultado = await workflow.execute_activity(
            fazer_deploy, pedido, start_to_close_timeout=timedelta(minutes=5)
        )
        self.estado = "concluído"
        return f"{resultado} (aprovado por {self.aprovador})"

    @workflow.update
    def registrar_pedido(self) -> str:
        return f"{self.estado} (pedido por {self.solicitante})"

    @workflow.update
    def aprovar(self, aprovacao: Aprovacao) -> str:
        self.aprovador = aprovacao.aprovador
        return f"aprovado por {aprovacao.aprovador}"

    @aprovar.validator
    def validar_aprovacao(self, aprovacao: Aprovacao) -> None:
        # Se o validador levanta erro, o update nem entra no histórico.
        if aprovacao.aprovador == self.solicitante:
            raise ValueError("quem pediu não pode aprovar o próprio deploy")
        if self.estado != "aguardando aprovação":
            raise ValueError(f"não dá para aprovar: estado atual é '{self.estado}'")

    @workflow.signal
    def rejeitar(self, quem: str) -> None:
        self.rejeitado_por = quem

    @workflow.query
    def status(self) -> str:
        return self.estado
