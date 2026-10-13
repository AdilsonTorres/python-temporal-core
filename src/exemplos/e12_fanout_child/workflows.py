"""Fan-out com concorrência limitada: lotes de N child workflows em paralelo."""

import asyncio
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import gerar_relatorio


@workflow.defn
class RelatorioWorkflow:
    """Filho: gera um relatório. Tem histórico, retries e id próprios."""

    @workflow.run
    async def run(self, numero: int) -> str:
        return await workflow.execute_activity(
            gerar_relatorio, numero, start_to_close_timeout=timedelta(minutes=1)
        )


@workflow.defn
class RelatoriosWorkflow:
    def __init__(self) -> None:
        self.prontos: list[str] = []
        self.total = 0

    @workflow.run
    async def run(self, total: int, lote: int = 3) -> list[str]:
        self.total = total
        pai = workflow.info().workflow_id
        for inicio in range(0, total, lote):
            numeros = range(inicio + 1, min(inicio + lote, total) + 1)
            # Espera o lote inteiro antes de começar o próximo: no máximo `lote` em paralelo.
            arquivos = await asyncio.gather(
                *(
                    workflow.execute_child_workflow(
                        RelatorioWorkflow.run, n, id=f"{pai}-relatorio-{n}"
                    )
                    for n in numeros
                )
            )
            self.prontos.extend(arquivos)
        return self.prontos

    @workflow.query
    def progresso(self) -> str:
        return f"{len(self.prontos)}/{self.total}"
