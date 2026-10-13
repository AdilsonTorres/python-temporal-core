from pydantic import BaseModel


class Lembrete(BaseModel):
    texto: str
    atraso_s: float = 60  # quanto falta para disparar
    soneca_s: float = 30  # quanto cada soneca adia
    espera_resposta_s: float = 300  # sem resposta depois do disparo: desiste
    max_sonecas_por_execucao: int = 3  # depois disso, continue_as_new
    sonecas: int = 0  # total acumulado (atravessa os continue_as_new)
    execucao: int = 1
