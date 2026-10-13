# e10 — Automação de rede com rollback

## Objetivo
Webhook (FastAPI) -> workflow com id = id do evento: valida no inventário, aplica a config, verifica; se a verificação falhar, reverte (saga) e notifica. Equipamentos simulados em memória.

| Conceito | Onde ver |
|---|---|
| Saga com compensação | `workflows.py` · `RenomearDispositivoWorkflow.run` |
| Webhook idempotente (id do evento = id do workflow) | `api.py` · `webhook_inventario` |
| Erro de negócio sem retry | `activities.py` · `non_retryable=True` |

## Como executar
```bash
make servidor     # terminal 1 (UI http://localhost:8233), se ainda não estiver de pé
make e10-worker            # terminal 2
make e10                   # sucesso: renomeado
make e10-falha             # verificação falha: revertido
make e10-api               # webhook em :8010 (curl no docstring de api.py)
```

## O que observar
- Reenviar o mesmo webhook não duplica o workflow.
- Na UI, `reverter_config` aparece só no caminho de falha.
