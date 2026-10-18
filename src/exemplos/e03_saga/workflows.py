"""SAGA: se um passo falha, desfaz os anteriores em ordem reversa."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import (
        Viagem,
        cancelar_carro,
        cancelar_hotel,
        cancelar_voo,
        reservar_carro,
        reservar_hotel,
        reservar_voo,
    )

TIMEOUT = timedelta(seconds=30)


@workflow.defn
class ReservaViagemWorkflow:
    @workflow.run
    async def run(self, viagem: Viagem) -> list[str]:
        compensacoes = []  # o que já foi feito e como desfazer
        try:
            voo = await workflow.execute_activity(
                reservar_voo, viagem, start_to_close_timeout=TIMEOUT
            )
            compensacoes.append((cancelar_voo, voo))

            hotel = await workflow.execute_activity(
                reservar_hotel, viagem, start_to_close_timeout=TIMEOUT
            )
            compensacoes.append((cancelar_hotel, hotel))

            carro = await workflow.execute_activity(
                reservar_carro, viagem, start_to_close_timeout=TIMEOUT
            )
            compensacoes.append((cancelar_carro, carro))

            return [voo, hotel, carro]
        except Exception:
            for cancelar, reserva in reversed(compensacoes):
                await workflow.execute_activity(cancelar, reserva, start_to_close_timeout=TIMEOUT)
            raise
