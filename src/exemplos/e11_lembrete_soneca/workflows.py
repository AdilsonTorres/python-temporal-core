"""Lembrete com soneca: o timeout do wait_condition é o timer, o predicado é o cancelamento."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import notificar
    from .modelos import Lembrete


@workflow.defn
class LembreteWorkflow:
    def __init__(self) -> None:
        self.dispensado = False
        self.soneca = False
        self.estado = "agendado"
        self.sonecas = 0

    @workflow.run
    async def run(self, lembrete: Lembrete) -> str:
        self.sonecas = lembrete.sonecas
        atraso = lembrete.atraso_s
        for _ in range(lembrete.max_sonecas_por_execucao):
            try:
                # Dispensou antes da hora? O predicado vira verdadeiro e o timer morre.
                await workflow.wait_condition(
                    lambda: self.dispensado, timeout=timedelta(seconds=atraso)
                )
                return "cancelado antes de disparar"
            except TimeoutError:
                pass  # o tempo passou: é hora de avisar

            self.estado = "disparado"
            await workflow.execute_activity(
                notificar, lembrete.texto, start_to_close_timeout=timedelta(seconds=10)
            )
            try:
                await workflow.wait_condition(
                    lambda: self.soneca or self.dispensado,
                    timeout=timedelta(seconds=lembrete.espera_resposta_s),
                )
            except TimeoutError:
                return "ignorado"
            if self.dispensado:
                return f"confirmado após {self.sonecas} sonecas ({lembrete.execucao} execuções)"
            self.soneca = False
            self.sonecas += 1
            self.estado = "adiado"
            atraso = lembrete.soneca_s

        # Histórico pequeno: recomeça do zero levando só o estado necessário.
        workflow.continue_as_new(
            lembrete.model_copy(
                update={
                    "atraso_s": atraso,
                    "sonecas": self.sonecas,
                    "execucao": lembrete.execucao + 1,
                }
            )
        )

    @workflow.signal
    def adiar(self) -> None:
        self.soneca = True

    @workflow.signal
    def dispensar(self) -> None:
        self.dispensado = True

    @workflow.query
    def status(self) -> str:
        return f"{self.estado} ({self.sonecas} sonecas)"
