"""Gate de deploy: o código novo precisa reproduzir os históricos gravados."""

import asyncio
from pathlib import Path

import pytest
from temporalio.client import WorkflowHistory
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Replayer
from temporalio.workflow import NondeterminismError

from exemplos.e08_versionamento.v2 import AssinaturaV2
from exemplos.e08_versionamento.v2_quebrado import AssinaturaV2Quebrado

HISTORICOS = sorted(Path(__file__).parent.joinpath("historicos").glob("*.json"))


async def reproduzir(workflow, arquivo: Path) -> None:
    history = WorkflowHistory.from_json(arquivo.stem, arquivo.read_text())
    replayer = Replayer(workflows=[workflow], data_converter=pydantic_data_converter)
    await asyncio.wait_for(replayer.replay_workflow(history), timeout=60)  # replay pode travar


def test_existem_historicos():
    assert HISTORICOS, "nenhum histórico em tests/historicos/ (rode gravar_historico)"


@pytest.mark.parametrize("arquivo", HISTORICOS, ids=lambda p: p.stem)
async def test_codigo_novo_reproduz_historico(arquivo):
    await reproduzir(AssinaturaV2, arquivo)


@pytest.mark.parametrize("arquivo", HISTORICOS, ids=lambda p: p.stem)
async def test_mudanca_sem_patched_e_barrada(arquivo):
    with pytest.raises(NondeterminismError):
        await reproduzir(AssinaturaV2Quebrado, arquivo)
