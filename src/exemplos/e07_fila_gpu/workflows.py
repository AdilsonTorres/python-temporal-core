"""Um workflow por prompt. Backend fora do ar não falha: a requisição espera e tenta de novo."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import gerar_resposta


@workflow.defn
class InferenciaWorkflow:
    @workflow.run
    async def run(self, prompt: str) -> str:
        return await workflow.execute_activity(
            gerar_resposta,
            prompt,
            start_to_close_timeout=timedelta(minutes=2),
            schedule_to_close_timeout=timedelta(hours=1),  # teto total da espera
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=0,  # tenta para sempre, até o schedule_to_close
            ),
        )
