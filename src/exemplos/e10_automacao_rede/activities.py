"""Activities simuladas: nada de equipamento real, só dicts em memória."""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from .modelos import EventoRede

INVENTARIO = {"sw-01": "switch", "rt-02": "roteador"}  # inventário falso: dispositivo -> tipo
EQUIPAMENTOS = {"sw-01": "sw-01", "rt-02": "rt-02"}  # hostname atual de cada equipamento


@activity.defn
async def validar_no_inventario(evento: EventoRede) -> str:
    if evento.dispositivo not in INVENTARIO:
        raise ApplicationError(f"{evento.dispositivo} não existe no inventário", non_retryable=True)
    print(
        f"✅ inventário conhece {evento.dispositivo} ({INVENTARIO[evento.dispositivo]})", flush=True
    )
    return INVENTARIO[evento.dispositivo]


@activity.defn
async def aplicar_config(evento: EventoRede) -> str:
    anterior = EQUIPAMENTOS[evento.dispositivo]
    EQUIPAMENTOS[evento.dispositivo] = evento.novo_nome
    print(f"🔧 {evento.dispositivo}: hostname {anterior} -> {evento.novo_nome}", flush=True)
    return anterior


@activity.defn
async def verificar(evento: EventoRede) -> None:
    if evento.falhar_verificacao:
        EQUIPAMENTOS[evento.dispositivo] = "???"  # o equipamento ficou em estado estranho
    atual = EQUIPAMENTOS[evento.dispositivo]
    if atual != evento.novo_nome:
        print(f"❌ verificação: esperava {evento.novo_nome}, achei {atual}", flush=True)
        raise ApplicationError("verificação falhou", non_retryable=True)
    print(f"✅ verificado: {evento.dispositivo} responde como {atual}", flush=True)


@activity.defn
async def reverter_config(evento: EventoRede, nome_anterior: str) -> None:
    EQUIPAMENTOS[evento.dispositivo] = nome_anterior
    print(f"↩️  rollback: {evento.dispositivo} voltou para {nome_anterior}", flush=True)


@activity.defn
async def notificar(mensagem: str) -> None:
    print(f"📣 {mensagem}", flush=True)
