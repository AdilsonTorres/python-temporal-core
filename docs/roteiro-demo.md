# Roteiro das demos ao vivo

Demo principal: e01 com `kill -9`. Backups, em ordem: e03, e04, e06, e07, e09.
Tudo roda na raiz do repositório com `make` (`make` lista os alvos). Versão Docker no fim de cada demo principal.
Ensaiados contra servidor real: e01, e03, e04, e06 (2026-10-12); e07, e08, e09 (2026-10-13).

## Checklist antes de subir ao palco

- [ ] Portas 7233 e 8233 livres (`ss -ltn | grep -E ':(7233|8233)'` sem saída).
- [ ] `make setup` feito; `make test` verde.
- [ ] Terminal A: `make servidor`. Na primeira vez baixa o CLI (cerca de 20 s): suba bem antes e espere a linha "Temporal rodando". Para parar: Ctrl+C.
- [ ] Aquecer: rode o e01 inteiro uma vez (`make e01 PEDIDO=aquecimento`), ou use IDs novos na demo.
- [ ] `export DEMORA_PASSO=3` nos terminais que sobem o worker do e01 (3 s por passo; use 4 ou 5 para plateia grande, sempre abaixo de 10, que é o timeout de cada passo). Depois do kill -9, o passo interrompido volta em até ~10 s: aproveite para mostrar a UI.
- [ ] Workers dos backups em background num terminal reserva: `make e03-worker`, `make e04-worker`, `make e06-worker`.
- [ ] Abas: UI em http://localhost:8233/namespaces/default/workflows, slides, página do workflow já aberta (reserva).
- [ ] Fonte grande (Ctrl + +), alto contraste, 3 painéis visíveis.
- [ ] IDs nunca reutilizados: sufixos `demo1`, `demo2`...
- [ ] Plano Docker pronto (se o ambiente local falhar): `make docker-build` feito antes, sem rede no palco.

## Demo principal: e01, sobrevivendo a `kill -9`

Terminais: B (worker), C (comandos), navegador na UI.

1. B: `make e01-worker`. Saída: `👷 worker de pedidos (pid NNNN) ...`. Anote o pid.
2. C: `make e01 PEDIDO=demo1`. Saída: `🚀 iniciado: pedido-demo1 (UI: ...)`
3. UI: o workflow `pedido-demo1` ganhando eventos. Diga: cada activity vira um evento no histórico.
4. B mostra `✅ validar`, `✅ cobrar`, `✅ reservar estoque`, `✅ enviar` (3 s entre eles). Quando aparecer `✅ enviar` (ou `reservar estoque`), em C: `kill -9 NNNN`.
   Diga: o workflow está vivo no servidor, ninguém está executando.
5. UI: ainda Running. Espere uns segundos em silêncio.
6. B: `make e01-worker` (novo processo).
7. Saída esperada:
   - worker 1: `validar`, `cobrar`, `reservar estoque`, `enviar`, todos `(tentativa 1)`
   - worker 2: `✅ enviar: pedido demo1 (tentativa 2)` e `✅ notificar cliente: pedido demo1 (tentativa 1)`
   - C: `🎉 concluído: {'pedido_id': 'demo1', 'pagamento_id': 'pag-demo1', 'rastreio': 'BR...'}`

   Ponto-chave: `validar_pedido` e `cobrar` NÃO aparecem no log do worker 2. Só o passo interrompido repete. Em produção, torne cada activity idempotente (com chave), porque esse passo pode rodar de novo.
8. UI: histórico, resultados guardados e o retry do passo interrompido.

Variação com retry: `make e01-falha` sobe o worker com `cobrar` falhando nas 2 primeiras tentativas (a 3ª passa), sem código de retry.

Versão Docker:

1. `make docker-up`, depois `make docker-e01` (sobe o worker e inicia o pedido 42; mude com `PEDIDO=demo1`).
2. `make docker-kill-e01` (kill -9 no container).
3. `docker compose --profile e01 up -d e01-worker` e confira em `docker compose logs e01-worker`.
4. Ao fim: `make docker-down`.

Se der errado: o worker novo não pegou o trabalho? Confira a task queue na UI (aba Workers do workflow) e se o worker subiu sem erro de conexão. Plano B: mostre o `pedido-ensaio` já concluído na UI e narre a sequência (ou o GIF `docs/media/demo-e01-kill.gif`); ou pule para o e03.

## Backup 1: e03, SAGA com compensação

Terminais: B worker, C comando.

1. B: `make e03-worker`
2. C: `make e03-falha`
3. Diga: voo e hotel reservados, o carro falha, o rollback roda em ordem reversa.
4. Worker: `✅ voo reservado para ...`, `✅ hotel reservado em ...`, `❌ carro: sem carros disponíveis`, `↩️ compensação: hotel-... cancelado`, `↩️ compensação: voo-... cancelado`. C: `💥 viagem falhou e foi desfeita: sem carros disponíveis`.
5. UI: compensações são activities no histórico, com retry. Se o worker cair no meio do rollback, ele continua.

Se der errado: `make e03` mostra o caminho feliz; ou abra a execução anterior na UI. A mesma falha vem de `FALHAR_CARRO=1` no ambiente do worker.

## Backup 2: e04, aprovação humana

Terminais: B worker, C comandos. Use um ID novo (`ID=deploy-d1`).

1. B: `make e04-worker`
2. C, em ordem:
   - `make e04-pedir ID=deploy-d1` -> `⏳ deploy-d1: aguardando aprovação (pedido por ana)`
   - `make e04-status ID=deploy-d1` (Query, não altera nada)
   - `make e04-aprovar ID=deploy-d1 QUEM=ana` -> `❌ update rejeitado: ValueError: quem pediu não pode aprovar o próprio deploy`
   - `make e04-aprovar ID=deploy-d1 QUEM=bruno` -> `✅ api-pagamentos@v2.3.0 no ar (aprovado por bruno)`
3. Diga: Update é síncrono e validado; o rejeitado nem entra no histórico (mostre na UI). Signal (`rejeitar`) é fire-and-forget. Timer durável de 3 dias rejeita sozinho.

Se der errado: `make e04-status` mostra o estado; se o workflow já concluiu, use outro ID. Sem worker, o `pedir` trava: confira o terminal B.

## Backup 3: e06, agente com aprovação

Terminais: B worker, C comandos. ID novo (`AGENTE=agente-d1`).

1. B: `make e06-worker`
2. C:
   - `make e06 AGENTE=agente-d1` -> `🤖 agente-d1: agente trabalhando`
   - `uv run python -m exemplos.e06_agente.cli pendencias agente-d1` -> `⏳ ["reiniciar_servico({'servico': 'api-pagamentos'})"]`
   - `make e06-aprovar AGENTE=agente-d1 QUEM=agente_ops` -> `❌ rejeitado: ValueError: o agente não pode aprovar as próprias ações`
   - `make e06-aprovar AGENTE=agente-d1 QUEM=bruno` -> `✅ aprovado por bruno` e `🤖 Resumo: reiniciar_servico -> api-pagamentos reiniciado, latência normalizada`
3. Diga: "nenhum agente deve poder ampliar os limites da própria autoridade". Na UI: cada chamada ao modelo e cada tool é uma activity; o LLM é um falso roteirizado (offline).
4. Opcional: `AGENTE_FALHAS_LLM=2 make e06-worker` simula o provedor de LLM caindo; os retries aparecem na UI e o agente conclui.

Se der errado: sem rede nem chave não é problema (LLM falso). Se `AGENTE_MODELO` estiver definido no shell por engano, `unset AGENTE_MODELO` e reinicie o worker.

## Backup 4: e07, fila de GPU (extra)

Terminais: B backend, C worker, D comandos.

1. B: `make e07-backend`
2. C: `make e07-worker`
3. D: `make e07`
4. Com os prompts em andamento, Ctrl+C no backend (B). UI: activities em retry, workflows continuam Running (não falham).
5. B: `make e07-backend` de novo. Todos terminam, um de cada vez; D imprime os resultados.

Se der errado: se o `make e07` terminou antes de matar o backend, rode de novo e mate mais cedo (`uv run python -m exemplos.e07_fila_gpu.iniciar 10` para mais prompts). Porta ocupada: `ss -ltn | grep 8001`.

## Backup 5: e09, benchmark (extra)

Terminais: B worker, C comando, D query.

1. B: `make e09-worker`
2. C: `make e09` (para o build sem GIL: `uv run python -m exemplos.e09_benchmark_python.iniciar --repeticoes 5 --free-threaded`)
3. D (requer o CLI do Temporal): `temporal workflow query --workflow-id <id impresso por iniciar> --name progresso`
4. Saída: tabela com tempo médio e speedup por versão do Python e benchmark, e a média dos speedups no fim.
5. Diga: fan-out com `asyncio.gather`, uma activity por medição, 1 por vez para não distorcer; se o worker cair, o já medido não repete.

Se der errado: a 1ª execução baixa interpretadores via uv (lento, precisa de rede). Rode antes da palestra para aquecer o cache; no palco use `--repeticoes 1`.

## Depois da demo

Ctrl+C em cada terminal, inclusive no servidor (`make servidor`). O servidor guarda o histórico em `temporal-dev.db` (ignorado pelo git); apague o arquivo para começar do zero. No Docker: `make docker-down`.
