"""Backend falso (formato Ollama).

uv run uvicorn exemplos.e07_fila_gpu.backend_falso:app --port 8001
"""

import asyncio

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Pedido(BaseModel):
    prompt: str


@app.post("/api/generate")
async def generate(pedido: Pedido) -> dict:
    await asyncio.sleep(2)  # "inferência"
    return {"response": f"eco: {pedido.prompt}"}
