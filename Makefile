# Atalhos para rodar os exemplos. `make` lista os alvos.
RUN = uv run python -m
ID ?= deploy-1
QUEM ?= bruno
AGENTE ?= agente-1
PEDIDO ?= a api-pagamentos está lenta
PEDIDO ?= 42
ESPERA ?= 20

.DEFAULT_GOAL := help
.PHONY: help setup servidor ui test lint todos

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Instala as dependências (uv sync)
	uv sync

servidor: ## Sobe o servidor Temporal local (gRPC 7233, UI http://localhost:8233)
	$(RUN) exemplos.servidor_dev

ui: ## Opcional, com Docker: UI 2.56 em http://localhost:8080 para o `make servidor`
	docker run --rm --network host -e TEMPORAL_ADDRESS=127.0.0.1:7233 -e TEMPORAL_UI_PORT=8080 \
		-e TEMPORAL_NAV_COLLAPSED_BY_DEFAULT=true -e TEMPORAL_DISABLE_NEWS_FETCH=true temporalio/ui:2.56.0

test: ## Roda os testes
	uv run pytest

lint: ## ruff check + ruff format --check
	uv run ruff check .
	uv run ruff format --check .

e01-worker: ## E01: worker do pedido
	$(RUN) exemplos.e01_pedido.worker
e01: ## E01: inicia o workflow do pedido (PEDIDO=42)
	$(RUN) exemplos.e01_pedido.iniciar $(PEDIDO)
e01-falha: ## E01: worker com pagamento falhando nas 2 primeiras tentativas
	FALHAR_PAGAMENTO=1 $(RUN) exemplos.e01_pedido.worker

e02-worker: ## E02: worker de idempotência
	$(RUN) exemplos.e02_idempotencia.worker
e02-api: ## E02: API de webhook (porta 8000)
	uv run uvicorn exemplos.e02_idempotencia.api:app --port 8000
e02: ## E02: inicia o workflow de idempotência
	$(RUN) exemplos.e02_idempotencia.iniciar

e03-worker: ## E03: worker da saga
	$(RUN) exemplos.e03_saga.worker
e03: ## E03: saga com sucesso
	$(RUN) exemplos.e03_saga.iniciar
e03-falha: ## E03: saga com falha no carro (compensações)
	$(RUN) exemplos.e03_saga.iniciar --falhar-carro

e04-worker: ## E04: worker de aprovação
	$(RUN) exemplos.e04_aprovacao.worker
e04-pedir: ## E04: pede deploy (ID=deploy-1)
	$(RUN) exemplos.e04_aprovacao.cli pedir $(ID)
e04-aprovar: ## E04: aprova (ID=deploy-1 QUEM=bruno)
	$(RUN) exemplos.e04_aprovacao.cli aprovar $(ID) $(QUEM)
e04-status: ## E04: consulta status (ID=deploy-1)
	$(RUN) exemplos.e04_aprovacao.cli status $(ID)

e05-worker: ## E05: worker de agendamentos
	$(RUN) exemplos.e05_agendamentos.worker
e05: ## E05: dispara os workflows do exemplo
	$(RUN) exemplos.e05_agendamentos.iniciar
e05-agendar: ## E05: cria o schedule
	$(RUN) exemplos.e05_agendamentos.agendar

e06-worker: ## E06: worker do agente
	$(RUN) exemplos.e06_agente.worker
e06: ## E06: pede ao agente (AGENTE=agente-1 PEDIDO="..."; LLM real: AGENTE_MODELO=claude-code no worker)
	$(RUN) exemplos.e06_agente.cli pedir $(AGENTE) "$(PEDIDO)"
e06-aprovar: ## E06: aprova ação pendente (AGENTE=agente-1 QUEM=bruno)
	$(RUN) exemplos.e06_agente.cli aprovar $(AGENTE) $(QUEM)
e06-pendencias: ## E06: mostra o que espera aprovação (AGENTE=agente-1)
	$(RUN) exemplos.e06_agente.cli pendencias $(AGENTE)

e07-backend: ## E07: backend LLM falso (porta 8001)
	uv run uvicorn exemplos.e07_fila_gpu.backend_falso:app --port 8001
e07-worker: ## E07: worker da fila de GPU
	$(RUN) exemplos.e07_fila_gpu.worker
e07: ## E07: dispara vários jobs
	$(RUN) exemplos.e07_fila_gpu.iniciar

e08-worker-v1: ## E08: worker versão 1
	$(RUN) exemplos.e08_versionamento.worker v1
e08-worker-v2: ## E08: worker versão 2
	$(RUN) exemplos.e08_versionamento.worker v2
e08: ## E08: inicia o workflow versionado (ESPERA=20 segundos de sono)
	$(RUN) exemplos.e08_versionamento.iniciar ana $(ESPERA)

replay: ## Roda o replay dos históricos gravados (gate de deploy)
	uv run pytest -q tests/test_replay.py

e09-worker: ## E09: worker do benchmark
	$(RUN) exemplos.e09_benchmark_python.worker
e09: ## E09: roda o benchmark entre versões do Python (10 rodadas; ARGS="--rodadas 2")
	$(RUN) exemplos.e09_benchmark_python.iniciar $(ARGS)

e10-worker: ## E10: worker da automação de rede
	$(RUN) exemplos.e10_automacao_rede.worker
e10: ## E10: renomeia um dispositivo (saga com sucesso)
	$(RUN) exemplos.e10_automacao_rede.iniciar
e10-falha: ## E10: verificação falha e a config é revertida
	$(RUN) exemplos.e10_automacao_rede.iniciar --falhar-verificacao
e10-api: ## E10: API do webhook (porta 8010)
	uv run uvicorn exemplos.e10_automacao_rede.api:app --port 8010

e11-worker: ## E11: worker do lembrete
	$(RUN) exemplos.e11_lembrete_soneca.worker
e11: ## E11: lembrete que soneca 3x e faz continue_as_new
	$(RUN) exemplos.e11_lembrete_soneca.iniciar

e12-worker: ## E12: worker do fan-out de relatórios
	$(RUN) exemplos.e12_fanout_child.worker
e12: ## E12: 10 relatórios em lotes de 3, com progresso
	$(RUN) exemplos.e12_fanout_child.iniciar

e13-worker: ## E13: worker do canário
	$(RUN) exemplos.e13_canario_worker.worker
e13: ## E13: roda o canário uma vez
	$(RUN) exemplos.e13_canario_worker.iniciar
e13-agendar: ## E13: cria o schedule do canário (a cada 30s)
	$(RUN) exemplos.e13_canario_worker.iniciar --agendar

e14-worker: ## E14: worker do carrinho
	$(RUN) exemplos.e14_entidade_carrinho.worker
e14: ## E14: abre, altera e fecha um carrinho por Updates
	$(RUN) exemplos.e14_entidade_carrinho.iniciar

todos: ## Roda todos os exemplos em sequência (popula a UI)
	bash scripts/rodar_todos.sh

# --- Docker (nada instalado além do Docker) ---
COMPOSE = docker compose
.PHONY: docker-build docker-up docker-e01 docker-kill-e01 docker-down

docker-build: ## Docker: constrói a imagem dos exemplos
	$(COMPOSE) --profile tools build

docker-up: ## Docker: sobe o servidor Temporal e a UI 2.56 (http://localhost:8233)
	$(COMPOSE) up -d --wait temporal ui

docker-e01: ## Docker: sobe o worker E01 e inicia um pedido
	$(COMPOSE) --profile e01 up -d e01-worker
	$(COMPOSE) --profile tools run --rm app python -m exemplos.e01_pedido.iniciar $(PEDIDO)

docker-kill-e01: ## Docker: mata o worker E01 (kill -9); religue com `docker compose --profile e01 up -d e01-worker`
	$(COMPOSE) --profile e01 kill -s SIGKILL e01-worker
	@echo "Religue: $(COMPOSE) --profile e01 up -d e01-worker"

docker-down: ## Docker: derruba tudo
	$(COMPOSE) --profile e01 --profile e02 --profile e03 --profile e04 --profile e05 --profile e06 --profile e07 --profile e08 --profile e10 --profile e11 --profile e12 --profile e13 --profile e14 --profile tools down --remove-orphans
