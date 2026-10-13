from pydantic import BaseModel


class EventoRede(BaseModel):
    evento_id: str  # id do webhook do inventário: vira o id do workflow
    dispositivo: str
    novo_nome: str
    falhar_verificacao: bool = False  # simula equipamento que não aplicou a config
