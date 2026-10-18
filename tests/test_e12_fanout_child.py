import uuid

from temporalio.worker import Worker

from exemplos.e12_fanout_child import activities as a
from exemplos.e12_fanout_child.workflows import RelatoriosWorkflow, RelatorioWorkflow


async def test_dez_relatorios_em_lotes_de_tres(env, monkeypatch):
    monkeypatch.setattr(a, "DEMORA", 0)
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client,
        task_queue=fila,
        workflows=[RelatoriosWorkflow, RelatorioWorkflow],
        activities=[a.gerar_relatorio],
    ):
        handle = await env.client.start_workflow(
            RelatoriosWorkflow.run, args=[10, 3], id=f"relatorios-{fila}", task_queue=fila
        )
        arquivos = await handle.result()
        assert arquivos == [f"relatorio-{n}.pdf" for n in range(1, 11)]
        assert await handle.query(RelatoriosWorkflow.progresso) == "10/10"
