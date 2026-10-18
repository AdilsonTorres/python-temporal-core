# e13 — Canário de workers

## Objetivo
Activity que consulta `DescribeTaskQueue(report_pollers=True)` e alerta se uma task queue não tem poller recente. A fila `fantasma` nunca tem worker.

| Conceito | Onde ver |
|---|---|
| Chamada gRPC direta ao servidor | `activities.py` · `idades_dos_pollers` |
| Regra de alerta pura (testável) | `activities.py` · `avaliar` |
| Schedule a cada 30s | `iniciar.py` · `--agendar` |

## Como executar
```bash
make servidor     # terminal 1 (UI http://localhost:8233), se ainda não estiver de pé
make e13-worker           # terminal 2
make e13                   # roda uma vez
make e13-agendar           # schedule a cada 30s
temporal schedule delete --schedule-id canario   # remove o schedule
```

## O que observar
- `canario: poller vivo` (✅) e `ALERTA` para `fantasma`.
- O servidor de testes (time-skipping) não implementa `DescribeTaskQueue`: o teste simula as idades.
