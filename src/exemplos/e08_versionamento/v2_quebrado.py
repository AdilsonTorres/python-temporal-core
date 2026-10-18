"""A mesma mudança SEM `patched`: quebra o replay de quem já estava dormindo."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import cobrar, enviar_lembrete, renovar
    from .modelos import Assinatura


@workflow.defn(name="AssinaturaWorkflow")
class AssinaturaV2Quebrado:
    @workflow.run
    async def run(self, assinatura: Assinatura) -> str:
        await workflow.execute_activity(
            cobrar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
        await workflow.execute_activity(
            enviar_lembrete, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )  # novo, sem patch
        await workflow.sleep(timedelta(seconds=assinatura.espera_segundos))
        return await workflow.execute_activity(
            renovar, assinatura, start_to_close_timeout=timedelta(seconds=30)
        )
