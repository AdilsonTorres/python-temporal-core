"""O "antes": retry, backoff e estado do pedido escritos à mão.

uv run python -m exemplos.e00_problema.fragil
"""

import random
import sqlite3
import time

db = sqlite3.connect("pedidos.db")
db.execute("CREATE TABLE IF NOT EXISTS pedidos (id TEXT PRIMARY KEY, passo TEXT)")


def chamar_api(nome: str) -> None:
    if random.random() < 0.3:
        raise ConnectionError("timeout")
    print(f"✅ {nome}")


def com_retry(nome: str) -> None:
    for tentativa in range(1, 6):
        try:
            chamar_api(nome)
            return
        except ConnectionError:
            print(f"❌ {nome}: falhou (tentativa {tentativa})")
            time.sleep(2**tentativa)  # e se o processo reiniciar aqui?
    raise RuntimeError(f"{nome}: desisti")


def salvar_passo(pedido_id: str, passo: str) -> None:
    db.execute("INSERT OR REPLACE INTO pedidos VALUES (?, ?)", (pedido_id, passo))
    db.commit()


def processar_pedido(pedido_id: str) -> None:
    linha = db.execute("SELECT passo FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    passo = linha[0] if linha else "novo"

    # Máquina de estados manual, para retomar de onde parou.
    if passo == "novo":
        com_retry("validar")
        salvar_passo(pedido_id, "validado")
        passo = "validado"
    if passo == "validado":
        com_retry("cobrar")  # caiu depois de cobrar e antes de salvar? Cobra de novo.
        salvar_passo(pedido_id, "cobrado")
        passo = "cobrado"
    if passo == "cobrado":
        try:
            com_retry("reservar_estoque")
        except RuntimeError:
            com_retry("estornar")  # e se o estorno falhar?
            raise
        salvar_passo(pedido_id, "reservado")
    # Falta: enviar, notificar, achar pedidos "presos", alertas, painel...


if __name__ == "__main__":
    processar_pedido("pedido-42")
