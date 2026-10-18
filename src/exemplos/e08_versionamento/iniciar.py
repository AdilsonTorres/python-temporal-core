"""uv run python -m exemplos.e08_versionamento.iniciar [cliente] [segundos_de_espera]"""

import sys

from exemplos.comum import conectar, rodar

from .modelos import Assinatura
from .v1 import AssinaturaV1
from .worker import TASK_QUEUE


async def main(cliente: str = "ana", *espera: str) -> None:
    assinatura = Assinatura(cliente=cliente)
    if espera:
        assinatura.espera_segundos = int(espera[0])
    client = await conectar()
    handle = await client.start_workflow(
        AssinaturaV1.run, assinatura, id=f"assinatura-{cliente}", task_queue=TASK_QUEUE
    )
    print(f"⏳ {handle.id} iniciado (dorme {assinatura.espera_segundos}s)")


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
