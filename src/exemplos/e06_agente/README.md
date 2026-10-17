# e06 — Agente de IA durável (Pydantic AI)

## Objetivo
Um agente que diagnostica um serviço e quer reiniciá-lo. Cada chamada ao LLM e cada tool é uma activity; a ação perigosa espera aprovação humana. Por padrão usa um LLM falso roteirizado (offline).

| Conceito | Onde ver |
|---|---|
| Agente como workflow | `workflows.py` · `AgenteOpsWorkflow` |
| Tools e LLM falso | `agente.py` · `consultar_status`, `reiniciar_servico`, `llm_falso` |
| Aprovação por Update com validador | `workflows.py` · `decidir` |
| Variante com tools via MCP | `agente_mcp.py`, `mcp_servidor.py` |
| CLI | `cli.py`; `iniciar.py` (gera ID novo) |

## Como executar
```bash
make servidor                            # terminal 1
make e06-worker                          # terminal 2
make e06 AGENTE=agente-1                 # terminal 3: pede ao agente
make e06-aprovar AGENTE=agente-1 QUEM=bruno
```
`QUEM=agente_ops` é rejeitado (o agente não aprova a si mesmo). Modelo real: `AGENTE_MODELO=ollama:qwen3:8b`; `AGENTE_FALHAS_LLM=2` simula falhas do LLM.

## O que observar
- Terminal: o agente para esperando aprovação; após o `bruno`, conclui.
- UI: activities de modelo e de tool no histórico; retries se `AGENTE_FALHAS_LLM` > 0.
- Workflow `Running` parado no `wait_condition` até a decisão.

![UI](../../../docs/media/e06_agente/ui.png)
![Terminal](../../../docs/media/e06_agente/terminal.gif)
