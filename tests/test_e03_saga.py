import uuid

from temporalio.client import WorkflowFailureError
from temporalio.worker import Worker

from exemplos.e03_saga import activities as a
from exemplos.e03_saga.worker import ACTIVITIES
from exemplos.e03_saga.workflows import ReservaViagemWorkflow


async def executar(env, monkeypatch, viagem):
    eventos = []
    monkeypatch.setattr(a, "avisar", eventos.append)  # captura as mensagens
    fila = str(uuid.uuid4())
    async with Worker(
        env.client, task_queue=fila, workflows=[ReservaViagemWorkflow], activities=ACTIVITIES
    ):
        try:
            resultado = await env.client.execute_workflow(
                ReservaViagemWorkflow.run, viagem, id=f"viagem-{fila}", task_queue=fila
            )
        except WorkflowFailureError as erro:
            resultado = erro
    return resultado, eventos


async def test_saga_sucesso(env, monkeypatch):
    resultado, eventos = await executar(env, monkeypatch, a.Viagem(id="1", destino="Floripa"))
    assert resultado == ["voo-1", "hotel-1", "carro-1"]
    assert not any("compensação" in e for e in eventos)


async def test_saga_compensa_em_ordem_reversa(env, monkeypatch):
    viagem = a.Viagem(id="2", destino="Floripa", falhar_carro=True)
    erro, eventos = await executar(env, monkeypatch, viagem)
    assert isinstance(erro, WorkflowFailureError)
    assert eventos == [
        "✅ voo reservado para Floripa",
        "✅ hotel reservado em Floripa",
        "❌ carro: sem carros disponíveis",
        "↩️ compensação: hotel-2 cancelado",  # desfaz em ordem reversa
        "↩️ compensação: voo-2 cancelado",  # o carro nunca foi reservado
    ]
