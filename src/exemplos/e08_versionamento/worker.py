"""Worker das assinaturas: escolha a versão do código.

uv run python -m exemplos.e08_versionamento.worker v1
uv run python -m exemplos.e08_versionamento.worker v2
"""

import sys

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import cobrar, enviar_lembrete, renovar
from .v1 import AssinaturaV1
from .v2 import AssinaturaV2

TASK_QUEUE = "assinaturas"
VERSOES = {"v1": AssinaturaV1, "v2": AssinaturaV2}


async def main(versao: str = "v2") -> None:
    worker = Worker(
        await conectar(),
        task_queue=TASK_QUEUE,
        workflows=[VERSOES[versao]],
        activities=[cobrar, enviar_lembrete, renovar],
    )
    print(f"⏳ worker de assinaturas ({versao}) rodando")
    await worker.run()


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
