from pydantic import BaseModel


class Assinatura(BaseModel):
    cliente: str
    espera_segundos: int = 30 * 24 * 3600  # 30 dias (na demo: use poucos segundos)
