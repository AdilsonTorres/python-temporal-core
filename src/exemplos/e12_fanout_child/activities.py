import asyncio
import os

from temporalio import activity

DEMORA = float(os.environ.get("DEMORA_RELATORIO", "1"))


@activity.defn
async def gerar_relatorio(numero: int) -> str:
    print(f"📄 gerando relatório {numero}...", flush=True)
    await asyncio.sleep(DEMORA)
    return f"relatorio-{numero}.pdf"
