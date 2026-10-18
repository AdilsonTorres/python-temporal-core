"""Timers duráveis: `sleep` de dias não segura processo, vira um timer no servidor."""

from datetime import timedelta

from pydantic import BaseModel
from temporalio import activity, workflow

TIMEOUT = timedelta(seconds=30)


class Lembrete(BaseModel):
    usuario: str
    mensagem: str
    em: timedelta


@activity.defn
async def enviar_mensagem(usuario: str, mensagem: str) -> None:
    print(f"📧 para {usuario}: {mensagem}", flush=True)


@activity.defn
async def gerar_relatorio_diario() -> str:
    print("📊 relatório diário gerado", flush=True)
    return "relatorio-ok"


@workflow.defn
class LembreteWorkflow:
    """Lembrete que pode ser adiado ou concluído por Signal."""

    def __init__(self) -> None:
        self.adiar_por: timedelta | None = None
        self.concluido = False

    @workflow.run
    async def run(self, lembrete: Lembrete) -> str:
        espera = lembrete.em
        while True:
            try:
                # Espera a hora chegar, mas acorda antes se chegar um Signal.
                await workflow.wait_condition(
                    lambda: self.adiar_por is not None or self.concluido, timeout=espera
                )
            except TimeoutError:
                break  # chegou a hora

            if self.concluido:
                return "concluído pelo usuário"
            espera = self.adiar_por
            self.adiar_por = None

        await workflow.execute_activity(
            enviar_mensagem,
            args=[lembrete.usuario, lembrete.mensagem],
            start_to_close_timeout=TIMEOUT,
        )
        return "lembrete enviado"

    @workflow.signal
    def adiar(self, por: timedelta) -> None:
        self.adiar_por = por

    @workflow.signal
    def concluir(self) -> None:
        self.concluido = True


@workflow.defn
class BoasVindasWorkflow:
    """Manda uma mensagem agora e outra 7 dias depois."""

    @workflow.run
    async def run(self, usuario: str) -> None:
        await workflow.execute_activity(
            enviar_mensagem, args=[usuario, "bem-vinda(o)!"], start_to_close_timeout=TIMEOUT
        )
        await workflow.sleep(timedelta(days=7))
        await workflow.execute_activity(
            enviar_mensagem,
            args=[usuario, "como está sendo sua primeira semana?"],
            start_to_close_timeout=TIMEOUT,
        )


@workflow.defn
class RelatorioDiarioWorkflow:
    """Disparado por um Schedule (veja agendar.py)."""

    @workflow.run
    async def run(self) -> str:
        return await workflow.execute_activity(
            gerar_relatorio_diario, start_to_close_timeout=timedelta(minutes=10)
        )
