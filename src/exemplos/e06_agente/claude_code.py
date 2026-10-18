"""LLM via Claude Code CLI local (já logado, sem API key), como um FunctionModel.

O CLI roda só como modelo de texto (sem tools próprias). As tools do agente são descritas
no system prompt e o modelo responde um JSON: {"tool": ..., "args": {...}} ou {"final": ...}.
"""

import asyncio
import json
import os
import re
import tempfile

from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

TIMEOUT = 100  # s; menor que o timeout da activity de modelo (120 s)

INSTRUCOES = """Você é o motor de decisão de um agente. Tools disponíveis:
{tools}

Responda APENAS com um objeto JSON, sem texto extra:
- para chamar uma tool: {{"tool": "<nome>", "args": {{...}}}}
- para encerrar: {{"final": "<resposta em português>"}}
Uma tool por vez. Use os resultados já presentes na conversa.

{instrucoes}"""


def montar_system_prompt(info: AgentInfo) -> str:
    tools = "\n".join(
        f"- {t.name}: {t.description or ''} | args (JSON schema): "
        + json.dumps(t.parameters_json_schema, ensure_ascii=False)
        for t in info.function_tools
    )
    return INSTRUCOES.format(tools=tools, instrucoes=info.instructions or "")


def montar_conversa(messages: list[ModelMessage]) -> str:
    """Histórico em texto simples, que vai no stdin do CLI."""
    linhas = []
    for m in messages:
        for p in m.parts:
            match p:
                case UserPromptPart():
                    linhas.append(f"[usuário] {p.content}")
                case ToolReturnPart():
                    linhas.append(f"[resultado de {p.tool_name}] {p.content}")
                case RetryPromptPart():
                    linhas.append(f"[erro, tente de novo] {p.content}")
                case ToolCallPart():
                    linhas.append(f"[você chamou] {p.tool_name}({p.args_as_dict()})")
                case TextPart():
                    linhas.append(f"[você] {p.content}")
    return "\n".join(linhas)


def interpretar(texto: str) -> ModelResponse:
    """JSON do modelo -> ToolCallPart ou TextPart. JSON inválido levanta (a activity repete)."""
    limpo = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    try:
        dados = json.loads(limpo)
    except ValueError as erro:
        raise ValueError(f"claude-code não devolveu JSON: {texto[:200]!r}") from erro
    if isinstance(dados, dict) and isinstance(dados.get("tool"), str):
        args = dados.get("args") or {}
        return ModelResponse(parts=[ToolCallPart(dados["tool"], args)])
    if isinstance(dados, dict) and isinstance(dados.get("final"), str):
        return ModelResponse(parts=[TextPart(dados["final"])])
    raise ValueError(f"JSON sem 'tool' nem 'final': {limpo[:200]!r}")


async def _chamar_cli(system_prompt: str, conversa: str) -> str:
    argv = [
        "claude", "-p", "--output-format", "json", "--tools", "", "--setting-sources", "",
        "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence",
        "--system-prompt", system_prompt,
    ]  # fmt: skip
    if modelo := os.environ.get("AGENTE_CLAUDE_MODELO"):
        argv += ["--model", modelo]
    with tempfile.TemporaryDirectory(prefix="agente-claude-") as cwd:  # cwd vazio: nada para ler
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            saida, _ = await asyncio.wait_for(proc.communicate(conversa.encode()), TIMEOUT)
        except BaseException:  # timeout ou cancelamento da activity
            proc.kill()
            await proc.wait()
            raise
    if proc.returncode != 0:
        raise RuntimeError(f"claude saiu com código {proc.returncode}")
    dados = json.loads(saida)
    if dados.get("is_error") or not isinstance(dados.get("result"), str):
        raise RuntimeError("claude-code reportou erro")
    return dados["result"]


async def llm_claude_code(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    texto = await _chamar_cli(montar_system_prompt(info), montar_conversa(messages))
    return interpretar(texto)


def modelo_claude_code() -> FunctionModel:
    return FunctionModel(llm_claude_code, model_name="claude-code")
