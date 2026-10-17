import json
import uuid

import pytest
from temporalio.worker import Worker

from exemplos.e09_benchmark_python import activities as a
from exemplos.e09_benchmark_python.iniciar import tabela
from exemplos.e09_benchmark_python.worker import ACTIVITIES
from exemplos.e09_benchmark_python.workflows import BenchmarkPythonWorkflow

# tempo falso por versão: 3.14 é 2x mais rápido que 3.13, 3.15 é 4x
FATOR = {"3.13": 1.0, "3.14": 0.5, "3.15": 0.25, "3.14t": 2.0}


@pytest.fixture
def falsos(monkeypatch):
    medidos: list[tuple[str, str]] = []
    instalados: list[str] = []

    async def instalar(versao):
        instalados.append(versao)
        return 0, ""

    async def medir(versao, nome, repeticoes):
        medidos.append((versao, nome))
        base = FATOR[versao]
        tempos = [base * 0.9, base * 1.1] * (repeticoes // 2)
        return 0, json.dumps({"versao_exata": f"{versao}.x", "tempos": tempos})

    monkeypatch.setattr(a, "_uv_python_install", instalar)
    monkeypatch.setattr(a, "_medir_em_subprocesso", medir)
    return medidos, instalados


async def _rodar(env, entrada):
    tq = str(uuid.uuid4())
    async with Worker(
        env.client, task_queue=tq, workflows=[BenchmarkPythonWorkflow], activities=ACTIVITIES
    ):
        return await env.client.execute_workflow(
            BenchmarkPythonWorkflow.run, entrada, id=f"bench-{tq}", task_queue=tq
        )


async def test_fan_out_e_speedup(env, falsos):
    medidos, instalados = falsos
    entrada = a.Entrada(repeticoes=4)
    r = await _rodar(env, entrada)

    assert sorted(medidos) == sorted((v, b) for v in entrada.versoes for b in entrada.benchmarks)
    assert sorted(instalados) == sorted(entrada.versoes)
    assert len(r.linhas) == 3 * len(a.BENCHMARKS)

    linha = next(x for x in r.linhas if x.versao == "3.14" and x.nome == "fib")
    assert linha.media_s == pytest.approx(0.5)
    assert linha.speedup == pytest.approx(2.0)
    assert "média" in tabela(r)


async def test_free_threaded_opcional(env, falsos):
    medidos, _ = falsos
    r = await _rodar(env, a.Entrada(repeticoes=2, benchmarks=["fib"], free_threaded=True))
    assert ("3.14t", "fib") in medidos
    assert set(r.versoes_exatas) == {"3.13", "3.14", "3.15", "3.14t"}
