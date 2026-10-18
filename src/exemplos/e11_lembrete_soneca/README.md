# e11 — Lembrete com soneca

## Objetivo
Lembrete que dispara, aceita soneca e confirmação por Signals e, após N sonecas, faz `continue_as_new` para manter o histórico pequeno.

| Conceito | Onde ver |
|---|---|
| Timer cancelável (`wait_condition` com timeout) | `workflows.py` · `LembreteWorkflow.run` |
| Signals `adiar` / `dispensar` e Query `status` | `workflows.py` |
| `continue_as_new` levando só o estado | `workflows.py` · fim de `run` |

## Como executar
```bash
make servidor     # terminal 1 (UI http://localhost:8233), se ainda não estiver de pé
make e11-worker           # terminal 2
make e11                   # soneca 3x (continue_as_new na 3ª) e confirma
```

## O que observar
- O run id muda após 2 sonecas, mas o workflow id é o mesmo.
- Resultado final: `confirmado após 3 sonecas (2 execuções)`.
