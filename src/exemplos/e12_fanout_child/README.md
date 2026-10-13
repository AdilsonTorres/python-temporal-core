# e12 — Fan-out com child workflows

## Objetivo
Gera 10 relatórios em lotes de 3: `asyncio.gather` sobre `execute_child_workflow`, com Query de progresso.

| Conceito | Onde ver |
|---|---|
| Child workflows (histórico e id próprios) | `workflows.py` · `RelatorioWorkflow` |
| Concorrência limitada por lotes | `workflows.py` · `RelatoriosWorkflow.run` |
| Query `progresso` | `workflows.py` · `progresso` |

## Como executar
```bash
make servidor     # terminal 1 (UI http://localhost:8233), se ainda não estiver de pé
make e12-worker           # terminal 2
make e12                   # DEMORA_RELATORIO ajusta a pausa (padrão 1s)
```

## O que observar
- Na UI, o pai com 10 filhos `<pai>-relatorio-N`, no máximo 3 ativos por vez.
- O terminal mostra o progresso `n/10`.
