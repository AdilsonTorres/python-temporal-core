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
    mediana_s: float
    variacao: float  # desvio padrão / mediana (0.03 = ±3%)
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

        # 2) rodadas intercaladas, cada uma em ordem embaralhada: o ruído da máquina se espalha
        pares = [(v, n) for v in versoes for n in entrada.benchmarks]
        self.total = len(pares) * entrada.rodadas
        tempos: dict[tuple[str, str], list[float]] = {p: [] for p in pares}
        exatas: dict[str, str] = {}
        for _ in range(entrada.rodadas):
            workflow.random().shuffle(pares)
            rodada = await asyncio.gather(*[self.medir(v, n, entrada.repeticoes) for v, n in pares])
            for m in rodada:
                tempos[m.versao, m.nome] += m.tempos
                exatas[m.versao] = m.versao_exata

        # 3) mediana (robusta a picos) e speedup contra a primeira versão
        mediana = {p: statistics.median(t) for p, t in tempos.items()}
        linhas = [
            Linha(
                versao=v,
                nome=n,
                mediana_s=mediana[v, n],
                variacao=statistics.pstdev(t) / mediana[v, n],
                speedup=mediana[versoes[0], n] / mediana[v, n],
            )
            for (v, n), t in tempos.items()
        ]
        exatas = {v: exatas[v] for v in versoes}  # colunas na ordem das versões
        return Resultado(base=versoes[0], linhas=linhas, versoes_exatas=exatas)
