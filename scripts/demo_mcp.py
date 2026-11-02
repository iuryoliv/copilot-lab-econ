"""Rehearsal via real MCP stdio; never represents a human approval or Copilot chat."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from econlab import analytics, core


async def execute(work: Path) -> dict:
    if work.exists():
        raise FileExistsError(f"Evidencias ja existem: {work}; escolha outro --run.")
    work.mkdir(parents=True)
    shutil.copytree(core.RAW, work / "data/raw")
    (work / "data/econ_lab.db").parent.mkdir(parents=True, exist_ok=True)
    with core.connect() as source, sqlite3.connect(work / "data/econ_lab.db") as target:
        source.backup(target)
    events = []
    env = {**os.environ, "ECONLAB_ROOT": str(work)}
    params = lambda name: StdioServerParameters(
        command=sys.executable, args=["-m", "econlab.server", name], env=env)
    async with AsyncExitStack() as stack:
        sessions = {}
        for name in ("sqlite-econ", "series-publicas", "analytics", "relatorios"):
            read, write = await stack.enter_async_context(stdio_client(params(name)))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            tools = await session.list_tools()
            sessions[name] = session
            events.append({"server": name, "tools": [t.model_dump(mode="json") for t in tools.tools]})

        async def call(server: str, tool: str, args: dict, error: bool = False):
            result = await sessions[server].call_tool(tool, args)
            events.append({"server": server, "tool": tool, "arguments": args,
                           "result": result.model_dump(mode="json")})
            analytics.save_json(work / "transport.json", {"events": events})
            if bool(result.isError) != error:
                raise AssertionError(f"{server}/{tool}: {result}")
            if error:
                return result
            if result.structuredContent is not None:
                return result.structuredContent
            return json.loads(result.content[0].text)

        before = await call("sqlite-econ", "listar_series", {})
        assert len(before["rows"]) == 7
        assert all(r["codigo_serie"] != "IBGE_PIMPF" for r in before["rows"])
        await call("sqlite-econ", "descrever_esquema", {})
        await call("sqlite-econ", "obter_serie", {"codigo": "BCB_433"})
        proposed = await call("series-publicas", "status_cache", {"codigo": "IBGE_PIMPF"})
        args = {"codigo": "IBGE_PIMPF", "proposta": proposed["proposta"]}
        await call("series-publicas", "ingerir_serie_cache", args, error=True)
        # A clearly labeled machine authorization ONLY in this rehearsal copy.
        original_root, original_db, original_raw, original_out = core.ROOT, core.DB, core.RAW, core.OUT
        try:
            core.ROOT, core.DB, core.RAW, core.OUT = work, work / "data/econ_lab.db", work / "data/raw", work / "outputs"
            authorization = core.approve("IBGE_PIMPF", proposed["proposta"],
                                         "automated-rehearsal-NOT-human")
        finally:
            core.ROOT, core.DB, core.RAW, core.OUT = original_root, original_db, original_raw, original_out
        events.append({"authorization": authorization, "human_approval": False})
        await call("series-publicas", "ingerir_serie_cache", args)
        await call("series-publicas", "ingerir_serie_cache", args, error=True)
        after = await call("sqlite-econ", "listar_series", {})
        assert len(after["rows"]) == 8
        await call("sqlite-econ", "consulta_sql", {"sql": "DROP TABLE observacoes"}, error=True)
        await call("sqlite-econ", "consulta_sql", {"sql": "SELECT 1; SELECT 2"}, error=True)
        await call("sqlite-econ", "consulta_sql", {"sql": "PRAGMA writable_schema=ON"}, error=True)
        preserved = await call("sqlite-econ", "consulta_sql", {
            "sql": "SELECT count(*) AS n FROM observacoes"})
        assert preserved["rows"][0]["n"] == 384
        inf = await call("analytics", "acumulado_12m", {})
        act = await call("analytics", "comparacao_trimestral", {"metodo": "STL"})
        await call("analytics", "ajuste_sazonal", {"metodo": "X-13"}, error=True)
        await call("analytics", "ajuste_sazonal", {"metodo": "STL"})
        await call("analytics", "resultados_validados", {"tipo": "inflacao"})
        await call("analytics", "resultados_validados", {"tipo": "atividade"})
        await call("relatorios", "listar_templates", {})
        report = await call("relatorios", "renderizar_relatorio", {})
    summary = {"executor": "Python MCP ClientSession + stdio, NAO chat Copilot",
               "human_approval": False, "authorization_scope": "copia isolada de ensaio",
               "db": str(work / "data/econ_lab.db"),
               "mcp_calls": sum("tool" in e for e in events),
               "inflacao": inf["ultimo"], "atividade": act["series"],
               "report": report, "events": events}
    analytics.save_json(work / "evidence.json", summary)
    return {k: v for k, v in summary.items() if k != "events"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="mcp-rehearsal")
    args = parser.parse_args()
    if not args.run.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Nome de ensaio simples, sem caminhos.")
    print(json.dumps(asyncio.run(execute(core.OUT / "evidence" / args.run)),
                     ensure_ascii=False, indent=2))
