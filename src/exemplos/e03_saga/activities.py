"""Reservas de viagem; cada reserva tem seu cancelamento (compensação)."""

import os

from pydantic import BaseModel
from temporalio import activity
from temporalio.exceptions import ApplicationError


class Viagem(BaseModel):
    id: str
    destino: str
    falhar_carro: bool = False


def avisar(msg: str) -> None:
    print(msg, flush=True)


@activity.defn
async def reservar_voo(viagem: Viagem) -> str:
    avisar(f"✅ voo reservado para {viagem.destino}")
    return f"voo-{viagem.id}"


@activity.defn
async def reservar_hotel(viagem: Viagem) -> str:
    avisar(f"✅ hotel reservado em {viagem.destino}")
    return f"hotel-{viagem.id}"


@activity.defn
async def reservar_carro(viagem: Viagem) -> str:
    if viagem.falhar_carro or os.environ.get("FALHAR_CARRO"):
        avisar("❌ carro: sem carros disponíveis")
        # Erro de negócio: repetir não adianta.
        raise ApplicationError("sem carros disponíveis", non_retryable=True)
    avisar(f"✅ carro reservado em {viagem.destino}")
    return f"carro-{viagem.id}"


@activity.defn
async def cancelar_voo(reserva: str) -> None:
    avisar(f"↩️ compensação: {reserva} cancelado")


@activity.defn
async def cancelar_hotel(reserva: str) -> None:
    avisar(f"↩️ compensação: {reserva} cancelado")


@activity.defn
async def cancelar_carro(reserva: str) -> None:
    avisar(f"↩️ compensação: {reserva} cancelado")
