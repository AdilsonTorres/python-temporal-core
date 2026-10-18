"""v2: lembrete antes de renovar, protegido por `workflow.patched`.

Execuções antigas seguem o caminho v1; novas enviam o lembrete.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import cobrar, enviar_lembrete, renovar
    from .modelos import Assinatura


@workflow.defn(name="AssinaturaWorkflow")
class AssinaturaV2:
    @workflow.run
    async def run(self, assinatura: Assinatura) -> str:
        await workflow.execute_activity(
            cobrar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
        await workflow.sleep(timedelta(seconds=assinatura.espera_segundos))
        if workflow.patched("lembrete-antes-de-renovar"):
            await workflow.execute_activity(
                enviar_lembrete, assinatura, start_to_close_timeout=timedelta(seconds=30)
            )
        return await workflow.execute_activity(
            renovar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
