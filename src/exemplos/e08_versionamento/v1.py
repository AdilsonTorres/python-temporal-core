"""v1 (em produção): cobrar, dormir, renovar."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import cobrar, renovar
    from .modelos import Assinatura


@workflow.defn(name="AssinaturaWorkflow")
class AssinaturaV1:
    @workflow.run
    async def run(self, assinatura: Assinatura) -> str:
        await workflow.execute_activity(
            cobrar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
        await workflow.sleep(timedelta(seconds=assinatura.espera_segundos))
        return await workflow.execute_activity(
            renovar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
