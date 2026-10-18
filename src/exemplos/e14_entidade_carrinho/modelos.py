from pydantic import BaseModel


class Item(BaseModel):
    sku: str
    quantidade: int
    preco: float


class Carrinho(BaseModel):
    cliente: str
    itens: dict[str, Item] = {}  # só é preenchido ao atravessar um continue_as_new
