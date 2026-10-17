from temporalio import activity

from .modelos import Assinatura


@activity.defn
async def cobrar(assinatura: Assinatura) -> str:
    print(f"💳 cobrança de {assinatura.cliente}", flush=True)
    return f"cobrança de {assinatura.cliente}"


@activity.defn
async def enviar_lembrete(assinatura: Assinatura) -> None:
    print(f"📧 lembrete enviado para {assinatura.cliente}", flush=True)


@activity.defn
async def renovar(assinatura: Assinatura) -> str:
    print(f"✅ {assinatura.cliente} renovado", flush=True)
    return f"{assinatura.cliente} renovado"
