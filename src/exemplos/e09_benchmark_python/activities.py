"""Activities: instalar um interpretador e medir um benchmark nele (subprocesso)."""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel
from temporalio import activity

SCRIPT = Path(__file__).with_name("benchmarks.py")
BENCHMARKS = ["nbody", "fib", "json", "regex", "comprehension"]


class Entrada(BaseModel):
    versoes: list[str] = ["3.13", "3.14", "3.15"]  # a primeira é a base do speedup
    benchmarks: list[str] = BENCHMARKS
    repeticoes: int = 5
    free_threaded: bool = False  # adiciona a variante 3.14t (sem GIL)


class Medicao(BaseModel):
    versao: str
    nome: str
    versao_exata: str
    tempos: list[float]


async def _executar(*comando: str) -> tuple[int, str]:
    """Roda o subprocesso e envia heartbeat enquanto espera."""
    proc = await asyncio.create_subprocess_exec(
        *comando, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    tarefa = asyncio.create_task(proc.communicate())
    while not tarefa.done():
        activity.heartbeat()
        await asyncio.wait({tarefa}, timeout=2)
    saida, _ = tarefa.result()
    return proc.returncode or 0, saida.decode()


async def _uv_python_install(versao: str) -> tuple[int, str]:
    return await _executar("uv", "python", "install", versao)


async def _medir_em_subprocesso(versao: str, nome: str, repeticoes: int) -> tuple[int, str]:
    # --no-project e -I: interpretador isolado, sem venv do projeto
    return await _executar(
        "uv", "run", "--no-project", "--python", versao, "python", "-I",
        str(SCRIPT), nome, str(repeticoes),
    )  # fmt: skip


@activity.defn
async def garantir_python(versao: str) -> str:
    codigo, saida = await _uv_python_install(versao)
    if codigo != 0:
        raise RuntimeError(f"uv python install {versao} falhou: {saida[-300:]}")
    return versao


@activity.defn
async def rodar_benchmark(versao: str, nome: str, repeticoes: int) -> Medicao:
    codigo, saida = await _medir_em_subprocesso(versao, nome, repeticoes)
    if codigo != 0:
        raise RuntimeError(f"benchmark {nome} em {versao} falhou: {saida[-300:]}")
    dados = json.loads(saida.strip().splitlines()[-1])
    return Medicao(
        versao=versao, nome=nome, versao_exata=dados["versao_exata"], tempos=dados["tempos"]
    )
