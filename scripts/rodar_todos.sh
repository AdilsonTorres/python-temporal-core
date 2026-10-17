#!/usr/bin/env bash
# Roda todos os exemplos em sequência (worker em background + cliente) para popular a UI.
# Pré-requisito: `make servidor` em outro terminal. e09 só com TODOS_COM_BENCHMARK=1.
# SOMENTE="e03 e04" roda apenas esses exemplos.
set -u
cd "$(dirname "$0")/.."

HOST=${TEMPORAL_HOST:-127.0.0.1}
PORTA=${TEMPORAL_PORTA:-7233}
if ! (exec 3<>"/dev/tcp/$HOST/$PORTA") 2>/dev/null; then
  echo "rode \`make servidor\` antes"
  exit 1
fi

RUN="uv run python -m"
RUN_ID=$(date +%H%M%S)
LOGS=$(mktemp -d)
export DEMORA_PASSO=1
PIDS=()
NOMES=()
STATUS=()

# Cada processo de fundo roda em seu próprio grupo (setsid) para matar uv + python juntos.
em_fundo() {
  setsid "$@" >>"$LOGS/fundo.log" 2>&1 &
  PIDS+=("$!")
  LAST_PID=$!
}
parar() {
  local pid
  for pid in "$@"; do
    kill -TERM -- "-$pid" 2>/dev/null
  done
  sleep 0.5
  for pid in "$@"; do
    kill -KILL -- "-$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
  done
}
limpar() {
  [ ${#PIDS[@]} -gt 0 ] && parar "${PIDS[@]}"
  rm -rf "$LOGS"
}
trap limpar EXIT
trap 'exit 130' INT TERM

# cli SEGUNDOS ARQUIVO_LOG cmd...: roda um cliente com timeout.
cli() {
  local seg=$1 log=$2
  shift 2
  timeout "$seg" "$@" >>"$log" 2>&1
}

# espera_wf ID SEGUNDOS: espera o workflow terminar com sucesso.
espera_wf() {
  timeout "$2" uv run python -I -c '
import asyncio, sys
from exemplos.comum import conectar
async def main():
    client = await conectar()
    await client.get_workflow_handle(sys.argv[1]).result()
asyncio.run(main())' "$1" >>"$LOGS/espera.log" 2>&1
}


e00() { cli 60 "$1" $RUN exemplos.e00_problema.fragil; }

e01() {
  em_fundo $RUN exemplos.e01_pedido.worker; local w=$LAST_PID
  sleep 3
  cli 90 "$1" $RUN exemplos.e01_pedido.iniciar "run$RUN_ID"
  local rc=$?
  parar "$w"
  return $rc
}

e02() {
  em_fundo $RUN exemplos.e02_idempotencia.worker; local w=$LAST_PID
  sleep 3
  cli 60 "$1" $RUN exemplos.e02_idempotencia.iniciar "evt_$RUN_ID"
  local rc=$?
  parar "$w"
  return $rc
}

e03() {
  em_fundo $RUN exemplos.e03_saga.worker; local w=$LAST_PID
  sleep 3
  cli 60 "$1" $RUN exemplos.e03_saga.iniciar && cli 60 "$1" $RUN exemplos.e03_saga.iniciar --falhar-carro
  local rc=$?
  parar "$w"
  return $rc
}

e04() {
  em_fundo $RUN exemplos.e04_aprovacao.worker; local w=$LAST_PID
  local id="deploy-$RUN_ID"
  sleep 3
  cli 30 "$1" $RUN exemplos.e04_aprovacao.cli pedir "$id" || { parar "$w"; return 1; }
  sleep 1
  cli 30 "$1" $RUN exemplos.e04_aprovacao.cli aprovar "$id" ana  # rejeição esperada
  grep -q "update rejeitado" "$1" || { parar "$w"; return 1; }
  cli 60 "$1" $RUN exemplos.e04_aprovacao.cli aprovar "$id" bruno
  local rc=$?
  grep -q "✅" "$1" || rc=1
  parar "$w"
  return $rc
}

e05() {
  em_fundo $RUN exemplos.e05_agendamentos.worker; local w=$LAST_PID
  sleep 3
  # o ID "lembrete-ana" é fixo: conclui um lembrete antigo ainda aberto
  timeout 20 uv run python -I -c '
import asyncio
from exemplos.comum import conectar
async def main():
    client = await conectar()
    await client.get_workflow_handle("lembrete-ana").signal("concluir")
asyncio.run(main())' >/dev/null 2>&1
  sleep 1
  cli 60 "$1" $RUN exemplos.e05_agendamentos.iniciar 3 && cli 60 "$1" $RUN exemplos.e05_agendamentos.agendar
  local rc=$?
  sleep 2
  parar "$w"
  return $rc
}

e06() {
  em_fundo $RUN exemplos.e06_agente.worker; local w=$LAST_PID
  local id="agente-$RUN_ID"
  sleep 4
  cli 30 "$1" $RUN exemplos.e06_agente.cli pedir "$id" "a api-pagamentos esta lenta" || { parar "$w"; return 1; }
  sleep 5
  cli 60 "$1" $RUN exemplos.e06_agente.cli aprovar "$id" bruno
  local rc=$?
  grep -q "rejeitado" "$1" && rc=1
  parar "$w"
  return $rc
}

e07() {
  em_fundo uv run uvicorn exemplos.e07_fila_gpu.backend_falso:app --port 8001; local b=$LAST_PID
  em_fundo $RUN exemplos.e07_fila_gpu.worker; local w=$LAST_PID
  sleep 4
  cli 90 "$1" $RUN exemplos.e07_fila_gpu.iniciar 3
  local rc=$?
  parar "$w" "$b"
  return $rc
}

e08() {
  local c1="v1-$RUN_ID" c2="v2-$RUN_ID" rc=0
  em_fundo $RUN exemplos.e08_versionamento.worker v1; local w=$LAST_PID
  sleep 3
  cli 30 "$1" $RUN exemplos.e08_versionamento.iniciar "$c1" 6 || rc=1
  sleep 2
  parar "$w"  # a execução fica dormindo, sem worker
  em_fundo $RUN exemplos.e08_versionamento.worker v2; w=$LAST_PID
  sleep 3
  espera_wf "assinatura-$c1" 60 || rc=1
  cli 30 "$1" $RUN exemplos.e08_versionamento.iniciar "$c2" 2 || rc=1
  espera_wf "assinatura-$c2" 60 || rc=1
  parar "$w"
  return $rc
}

e09() {
  if [ "${TODOS_COM_BENCHMARK:-}" != "1" ]; then
    echo "e09 pulado (use TODOS_COM_BENCHMARK=1)" >"$1"
    return 99
  fi
  em_fundo $RUN exemplos.e09_benchmark_python.worker; local w=$LAST_PID
  sleep 3
  cli 580 "$1" $RUN exemplos.e09_benchmark_python.iniciar --repeticoes 1
  local rc=$?
  parar "$w"
  return $rc
}

for n in ${SOMENTE:-e00 e01 e02 e03 e04 e05 e06 e07 e08 e09}; do
  echo "▶ $n"
  "$n" "$LOGS/$n.log"
  rc=$?
  NOMES+=("$n")
  case $rc in
    0) STATUS+=("ok") ;;
    99) STATUS+=("pulado") ;;
    *) STATUS+=("falhou") ;;
  esac
done

echo
echo "Resumo (UI: http://localhost:8233)"
falhas=0
for i in "${!NOMES[@]}"; do
  case ${STATUS[$i]} in
    ok) printf '  \033[32m✅ %s\033[0m\n' "${NOMES[$i]}" ;;
    pulado) printf '  \033[33m⏭  %s (pulado)\033[0m\n' "${NOMES[$i]}" ;;
    *)
      printf '  \033[31m❌ %s\033[0m\n' "${NOMES[$i]}"
      tail -n 5 "$LOGS/${NOMES[$i]}.log" 2>/dev/null | sed 's/^/       /'
      falhas=1
      ;;
  esac
done
exit $falhas
