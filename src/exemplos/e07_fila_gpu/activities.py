"""Activity que chama o backend de LLM local (formato Ollama) via HTTP."""

import asyncio
import os

import httpx
from temporalio import activity
from temporalio.exceptions import ApplicationError

LLM_BACKEND_URL = os.environ.get("LLM_BACKEND_URL", "http://localhost:8001")


async def _chamar_backend(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as http:
        resposta = await http.post(f"{LLM_BACKEND_URL}/api/generate", json={"prompt": prompt})
        resposta.raise_for_status()
        return resposta.json()["response"]


async def _batimento() -> None:
    while True:
        activity.heartbeat()
        await asyncio.sleep(5)


@activity.defn
async def gerar_resposta(prompt: str) -> str:
    batimento = asyncio.create_task(_batimento())  # avisa o Temporal que está viva
    try:
        return await _chamar_backend(prompt)
    except httpx.TransportError as erro:
        print("❌ backend fora do ar, tentando de novo...", flush=True)
        # erro curto e legível na UI (o traceback do httpx é enorme); continua retentável
        raise ApplicationError(f"backend fora do ar: {erro}") from None
    finally:
        batimento.cancel()
