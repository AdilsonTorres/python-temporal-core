"""Micro benchmarks em Python puro, rodados pelo interpretador de cada versão.

uv run --no-project --python 3.14 python -I benchmarks.py fib 3
Imprime um JSON: versão exata e o tempo (s) de cada repetição.
"""

import json
import re
import sys
import time


def nbody() -> float:
    corpos = [[0, 0, 0, 0, 39.5], [4.8, -1.1, 0.6, 2.8, 0.04], [8.3, 4.1, -1.0, 1.8, 0.01]]
    for _ in range(40_000):
        for a in corpos:
            for b in corpos:
                if a is not b:
                    dx, dy = a[0] - b[0], a[1] - b[1]
                    forca = 0.01 * b[4] / (dx * dx + dy * dy + 0.01) ** 1.5
                    a[2] -= dx * forca
                    a[3] -= dy * forca
        for c in corpos:
            c[0] += 0.01 * c[2]
            c[1] += 0.01 * c[3]
    return corpos[0][0]


def fib(n: int = 27) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def json_ida_volta() -> int:
    dados = [
        {"id": i, "nome": f"item-{i}", "tags": ["a", "b"], "preco": i * 1.5} for i in range(2_000)
    ]
    for _ in range(20):
        dados = json.loads(json.dumps(dados))
    return len(dados)


def regex() -> int:
    texto = " ".join(f"usuario{i}@exemplo.com.br tel 11-9{i:04d}" for i in range(5_000))
    return len(re.findall(r"(\w+)@(\w+)\.com\.br\s+tel\s+(\d{2})-(\d+)", texto))


def comprehension() -> int:
    total = 0
    for _ in range(10):
        quadrados = [i * i for i in range(100_000)]
        total += sum(q for q in quadrados if q % 3 == 0)
    return total


BENCHMARKS = {
    "nbody": nbody,
    "fib": fib,
    "json": json_ida_volta,
    "regex": regex,
    "comprehension": comprehension,
}

if __name__ == "__main__":
    funcao = BENCHMARKS[sys.argv[1]]
    funcao()  # aquecimento
    tempos = []
    for _ in range(int(sys.argv[2])):
        inicio = time.perf_counter()
        funcao()
        tempos.append(time.perf_counter() - inicio)
    print(json.dumps({"versao_exata": sys.version.split()[0], "tempos": tempos}))
