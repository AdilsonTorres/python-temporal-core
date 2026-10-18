from pydantic import BaseModel


class Pedido(BaseModel):
    id: str
    cliente: str
    itens: list[str]
    valor: float


class ResultadoPedido(BaseModel):
    pedido_id: str
    pagamento_id: str
    rastreio: str
