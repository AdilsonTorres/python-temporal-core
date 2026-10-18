"""Grava o histórico de um workflow em tests/historicos/ (insumo do gate de deploy).

1. make e08-worker-v1 e make e08 (workflow em produção)
2. uv run python -m exemplos.e08_versionamento.gravar_historico <workflow_id> [nome]
"""

import sys
from pathlib import Path

from exemplos.comum import conectar, rodar

PASTA = Path(__file__).parents[3] / "tests" / "historicos"


async def main(workflow_id: str, nome: str = "assinatura_gravada") -> None:
    client = await conectar()
    history = await client.get_workflow_handle(workflow_id).fetch_history()
    PASTA.mkdir(exist_ok=True)
    destino = PASTA / f"{nome}.json"
    destino.write_text(history.to_json())
    print(f"💾 {len(history.events)} eventos em {destino}")


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
