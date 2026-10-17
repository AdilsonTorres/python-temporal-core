"""Activities: os passos que falam com o mundo externo (podem falhar e repetir)."""

import asyncio
import os

from temporalio import activity

from .modelos import Pedido

# Pausa em cada passo: dá tempo de matar o worker (kill -9) durante a demo.
DEMORA = float(os.environ.get("DEMORA_PASSO", "3"))


async def anunciar(passo: str, pedido: Pedido) -> None:
    print(f"✅ {passo}: pedido {pedido.id} (tentativa {activity.info().attempt})", flush=True)
    await asyncio.sleep(DEMORA)


@activity.defn
async def validar_pedido(pedido: Pedido) -> None:
    await anunciar("validar", pedido)
    if not pedido.itens:
        raise ValueError("pedido sem itens")


@activity.defn
async def cobrar(pedido: Pedido) -> str:
    # FALHAR_PAGAMENTO=1: o gateway falha nas 2 primeiras tentativas.
    if os.environ.get("FALHAR_PAGAMENTO") and activity.info().attempt < 3:
        print(f"❌ cobrar: pedido {pedido.id} (tentativa {activity.info().attempt})", flush=True)
        raise ConnectionError("gateway de pagamento: timeout")
    await anunciar("cobrar", pedido)
    return f"pag-{pedido.id}"


@activity.defn
async def reservar_estoque(pedido: Pedido) -> None:
    await anunciar("reservar estoque", pedido)


@activity.defn
async def enviar(pedido: Pedido) -> str:
    await anunciar("enviar", pedido)
    return f"BR{pedido.id}"  # código de rastreio


@activity.defn
async def notificar_cliente(pedido: Pedido, rastreio: str) -> None:
    await anunciar("notificar cliente", pedido)
