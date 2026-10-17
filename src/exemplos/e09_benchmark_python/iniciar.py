"""uv run python -m exemplos.e09_benchmark_python.iniciar [--repeticoes N] [--free-threaded]

Progresso (outro terminal): temporal workflow query --workflow-id <id> --name progresso
"""

import argparse
import statistics
import uuid

from exemplos.comum import conectar, rodar

from .activities import Entrada
from .worker import TASK_QUEUE
from .workflows import BenchmarkPythonWorkflow, Resultado


def tabela(r: Resultado) -> str:
    versoes = list(r.versoes_exatas)
    nomes = list(dict.fromkeys(linha.nome for linha in r.linhas))
    linhas = {(linha.versao, linha.nome): linha for linha in r.linhas}

    saida = [f"{'benchmark':<15}" + "".join(f"{'🐍 ' + v:>18}" for v in versoes)]
    for nome in nomes:
        celulas = ""
        for v in versoes:
            linha = linhas[v, nome]
            celulas += f"{linha.media_s * 1000:9.1f}ms {linha.speedup:4.2f}x"
        saida.append(f"{nome:<15}{celulas}")

    celulas = ""
    for v in versoes:
        media = statistics.fmean(linhas[v, n].speedup for n in nomes)
        celulas += f"{'':>11}{media:4.2f}x"
    saida.append(f"{'média':<15}{celulas}")
    saida.append(f"speedup contra py{r.base} (>1 = mais rápido)")
    return "\n".join(saida)


async def main(repeticoes: int, free_threaded: bool) -> None:
    client = await conectar()
    entrada = Entrada(repeticoes=repeticoes, free_threaded=free_threaded)
    wf_id = f"benchmark-python-{uuid.uuid4().hex[:6]}"
    print(f"⏳ {wf_id}: medindo...")
    resultado = await client.execute_workflow(
        BenchmarkPythonWorkflow.run, entrada, id=wf_id, task_queue=TASK_QUEUE
    )
    print("✅ pronto\n")
    print(tabela(resultado))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--free-threaded", action="store_true")
    args = parser.parse_args()
    rodar(main(args.repeticoes, args.free_threaded))
