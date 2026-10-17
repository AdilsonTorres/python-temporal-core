"""Envia o mesmo evento 3 vezes: só um workflow é criado.

uv run python -m exemplos.e02_idempotencia.iniciar [evento_id]
"""

import sys

from exemplos.comum import conectar, rodar

from .api import iniciar_pagamento
from .workflows import EventoPagamento


async def main(evento_id: str) -> None:
    client = await conectar()
    evento = EventoPagamento(evento_id=evento_id, pedido_id="42", valor=350)
    ids = set()
    for vez in (1, 2, 3):
        resposta = await iniciar_pagamento(client, evento)
        ids.add(resposta["workflow_id"])
        print(f"📨 entrega {vez}: {resposta}")
    print(f"✅ 3 entregas, {len(ids)} workflow: {ids.pop()}")


if __name__ == "__main__":
    rodar(main(sys.argv[1] if len(sys.argv) > 1 else "evt_123"))
