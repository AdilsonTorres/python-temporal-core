"""Workflow curto, pensado para rodar num Schedule a cada poucos segundos."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import checar_filas


@workflow.defn
class CanarioWorkflow:
    @workflow.run
    async def run(self, filas: list[str], janela_s: int = 60) -> list[str]:
        return await workflow.execute_activity(
            checar_filas, args=[filas, janela_s], start_to_close_timeout=timedelta(seconds=30)
        )
