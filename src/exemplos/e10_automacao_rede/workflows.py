"""SAGA de rede: aplica a config, verifica e, se der errado, desfaz."""

from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from .activities import (
        aplicar_config,
        notificar,
        reverter_config,
        validar_no_inventario,
        verificar,
    )
    from .modelos import EventoRede

TIMEOUT = timedelta(seconds=30)


@workflow.defn
class RenomearDispositivoWorkflow:
    @workflow.run
    async def run(self, evento: EventoRede) -> str:
        await workflow.execute_activity(
            validar_no_inventario, evento, start_to_close_timeout=TIMEOUT
        )
        anterior = await workflow.execute_activity(
            aplicar_config, evento, start_to_close_timeout=TIMEOUT
        )
        try:
            await workflow.execute_activity(verificar, evento, start_to_close_timeout=TIMEOUT)
        except ActivityError:
            # Compensação: devolve o equipamento ao estado anterior.
            await workflow.execute_activity(
                reverter_config, args=[evento, anterior], start_to_close_timeout=TIMEOUT
            )
            msg = f"{evento.dispositivo}: renomear falhou, config revertida"
            await workflow.execute_activity(notificar, msg, start_to_close_timeout=TIMEOUT)
            return "revertido"

        msg = f"{evento.dispositivo} agora se chama {evento.novo_nome}"
        await workflow.execute_activity(notificar, msg, start_to_close_timeout=TIMEOUT)
        return "renomeado"
