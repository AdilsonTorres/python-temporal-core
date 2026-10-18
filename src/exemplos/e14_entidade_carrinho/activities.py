from temporalio import activity


@activity.defn
async def registrar_pedido(cliente: str, total: float) -> None:
    print(f"🧾 pedido de {cliente} registrado: R$ {total:.2f}", flush=True)
