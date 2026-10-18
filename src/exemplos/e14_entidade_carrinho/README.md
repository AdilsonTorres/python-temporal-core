# e14 — Entidade: carrinho de compras

## Objetivo
Um carrinho é um workflow vivo, alterado por Updates com validador. Fecha no `fechar` ou após 1 dia ocioso.

| Conceito | Onde ver |
|---|---|
| Updates com validador (recusa não entra no histórico) | `workflows.py` · `adicionar`, `remover` |
| Query `total` | `workflows.py` · `total` |
| Ocioso por 1 dia = timeout do `wait_condition` | `workflows.py` · `run` |
| `continue_as_new` após `all_handlers_finished` | `workflows.py` · `run` |

## Como executar
```bash
make servidor     # terminal 1 (UI http://localhost:8233), se ainda não estiver de pé
make e14-worker           # terminal 2
make e14
```

## O que observar
- O update recusado pelo validador não aparece no History.
- Resultado final: `fechado: R$ 250.00`.
