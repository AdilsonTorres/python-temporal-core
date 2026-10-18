from temporalio import activity


@activity.defn
async def notificar(texto: str) -> None:
    print(f"⏰ {texto}", flush=True)
