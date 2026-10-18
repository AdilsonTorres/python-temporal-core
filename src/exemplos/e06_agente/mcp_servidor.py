"""Servidor MCP mínimo (stdio), iniciado pelo agente_mcp."""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ops")


@mcp.tool()
def consultar_status(servico: str) -> str:
    return f"{servico}: degradado (via MCP, p99 = 4.2s)"


if __name__ == "__main__":
    mcp.run()
