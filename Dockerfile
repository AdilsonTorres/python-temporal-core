# Imagem dos exemplos: uv + Python 3.14, dependências travadas no uv.lock.
FROM ghcr.io/astral-sh/uv:0.9.30-python3.14-bookworm-slim

ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=manual
WORKDIR /app

# Camada de dependências (só invalida quando pyproject/uv.lock mudam)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Código dos exemplos
COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-c", "print('Use: docker compose run --rm app python -m exemplos.e01_pedido.iniciar')"]
