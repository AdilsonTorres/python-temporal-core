"""Fan-out de (versão x benchmark): uma activity por medição.

Se o worker cair, o que já foi medido fica no histórico e não roda de novo.
"""

import asyncio
import statistics
from datetime import timedelta

from pydantic import BaseModel
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import Entrada, Medicao, garantir_python, rodar_benchmark

RETRY = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=5))


class Linha(BaseModel):
    versao: str
    nome: str
    media_s: float
    speedup: float  # >1 = mais rápido que a base


class Resultado(BaseModel):
    base: str
    linhas: list[Linha]
    versoes_exatas: dict[str, str]


@workflow.defn
class BenchmarkPythonWorkflow:
    def __init__(self) -> None:
        self.concluidos = 0
        self.total = 0

    @workflow.query
    def progresso(self) -> str:
        return f"{self.concluidos}/{self.total} medições"

    async def medir(self, versao: str, nome: str, repeticoes: int) -> Medicao:
        medicao = await workflow.execute_activity(
            rodar_benchmark,
            args=[versao, nome, repeticoes],
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RETRY,
        )
        self.concluidos += 1
        return medicao

    @workflow.run
    async def run(self, entrada: Entrada) -> Resultado:
        versoes = list(entrada.versoes)
        if entrada.free_threaded:
            versoes.append("3.14t")
        self.total = len(versoes) * len(entrada.benchmarks)

        # 1) instala os interpretadores (o download não entra na medição)
        await asyncio.gather(
            *[
                workflow.execute_activity(
                    garantir_python,
                    versao,
                    start_to_close_timeout=timedelta(minutes=10),
                    heartbeat_timeout=timedelta(seconds=30),
                    retry_policy=RETRY,
                )
                for versao in versoes
            ]
        )

        # 2) mede tudo em paralelo (o worker executa uma por vez)
        medicoes = await asyncio.gather(
            *[
                self.medir(versao, nome, entrada.repeticoes)
                for versao in versoes
                for nome in entrada.benchmarks
            ]
        )

        # 3) média por benchmark e speedup contra a primeira versão
        medias = {(m.versao, m.nome): statistics.fmean(m.tempos) for m in medicoes}
        linhas = []
        for m in medicoes:
            media = medias[m.versao, m.nome]
            speedup = medias[versoes[0], m.nome] / media
            linhas.append(Linha(versao=m.versao, nome=m.nome, media_s=media, speedup=speedup))
        exatas = {m.versao: m.versao_exata for m in medicoes}
        return Resultado(base=versoes[0], linhas=linhas, versoes_exatas=exatas)
