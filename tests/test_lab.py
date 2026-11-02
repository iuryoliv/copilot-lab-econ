from __future__ import annotations

import asyncio
import ast
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import zipfile
from contextlib import closing
from decimal import Decimal

import pandas as pd
import pytest
from docx import Document
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

from econlab import analytics, core, reports


def synthetic(n=48, value=1.0):
    """SYNTHETIC test fixture, never published as observed public data."""
    return pd.DataFrame({"data_ref": pd.date_range("2022-01-01", periods=n, freq="MS")
                         .strftime("%Y-%m-%d"), "valor": [value] * n})


@pytest.mark.parametrize("kind", ["gap", "duplicate", "null", "infinity", "day", "noniso", "text"])
def test_invalid_monthly(kind):
    df = synthetic()
    if kind == "gap":
        df = df.drop(20)
    elif kind == "duplicate":
        df.loc[20, "data_ref"] = df.loc[19, "data_ref"]
    elif kind == "null":
        df.loc[20, "valor"] = float("nan")
    elif kind == "infinity":
        df.loc[20, "valor"] = float("inf")
    elif kind == "day":
        df.loc[20, "data_ref"] = "2023-09-02"
    elif kind == "noniso":
        df.loc[20, "data_ref"] = "2023-9-01"
    else:
        df["valor"] = df.valor.astype(object)
        df.loc[20, "valor"] = "indisponivel"
    with pytest.raises((ValueError, TypeError)):
        core.monthly(df)


def test_sorting_and_47_months():
    df = synthetic(47).iloc[::-1]
    result = analytics.accumulated(df)
    assert len(result) == 36
    expected = float((Decimal("1.01") ** 12 - 1) * 100)
    assert result.valor.iloc[-1] == pytest.approx(expected, abs=1e-10)
    assert result.data_ref.is_monotonic_increasing
    assert analytics.accumulated(synthetic(value=0)).valor.eq(0).all()


def test_rolling_gap_and_bad_rates():
    with pytest.raises(ValueError, match="Lacuna"):
        analytics.accumulated(synthetic(13).drop(5))
    with pytest.raises(ValueError):
        analytics.accumulated(synthetic(11))
    with pytest.raises(ValueError):
        analytics.accumulated(synthetic(value=-100))


def test_initial_catalog_and_official_metadata(lab):
    result = core.sql_read("SELECT * FROM series")
    assert len(result["rows"]) == 7
    assert not any(r["codigo_serie"] == "IBGE_PIMPF" for r in result["rows"])
    pim, meta = core.cache("IBGE_PIMPF")
    assert len(pim) == 48
    assert (meta["tabela"], meta["variavel"], meta["categoria"]) == (8888, 12606, 129314)
    pmc = core.catalog()["IBGE_PMC"]
    assert (pmc["tabela"], pmc["variavel"], pmc["categoria"]) == (8880, 7169, 56734)
    assert core.series("BCB_24364")[1]["ajuste_sazonal"] == "sim"
    assert core.series("BCB_24363")[1]["ajuste_sazonal"] == "nao"
    assert core.series("BCB_4189")[1]["unidade"] == "% a.a."
    assert core.series("BCB_3698")[1]["unidade_oficial"] == "c.m.u./US$"
    assert all(core.cache(code)[0].data_ref.is_monotonic_increasing for code in core.catalog())


def test_missing_db_never_created(lab, monkeypatch):
    absent = lab / "data/typo.db"
    monkeypatch.setattr(core, "DB", absent)
    with pytest.raises(FileNotFoundError):
        core.sql_read("SELECT 1")
    assert not absent.exists()


@pytest.mark.parametrize("sql", [
    "DROP TABLE observacoes", "DELETE FROM observacoes",
    "UPDATE observacoes SET valor=0", "CREATE TABLE evil(x)",
    "ATTACH DATABASE ':memory:' AS evil", "PRAGMA writable_schema=ON",
    "PRAGMA table_info(observacoes)", "SELECT 1; SELECT 2",
    "SELECT load_extension('evil')", "SELECT * FROM autorizacoes",
    "SELECT randomblob(1000000000)", "VACUUM",
    "WITH v AS (SELECT 1) DELETE FROM observacoes WHERE valor IN v",
])
def test_sql_rejections_effective_readonly(lab, sql):
    before = core.digest(core.DB)
    with pytest.raises((sqlite3.Error, ValueError)):
        core.sql_read(sql)
    assert core.digest(core.DB) == before
    assert core.sql_read("SELECT count(*) AS n FROM observacoes")["rows"][0]["n"] == 336
    assert '"outcome": "error"' in (lab / "logs/audit.jsonl").read_text()


def test_sql_bounds_and_deadline(lab):
    assert len(core.sql_read("SELECT * FROM observacoes", 3)["rows"]) == 3
    assert core.sql_read("SELECT * FROM observacoes", 3)["truncated"]
    with pytest.raises(ValueError):
        core.sql_read("SELECT 1", 5001)
    with pytest.raises(sqlite3.Error, match="interrupted"):
        core.sql_read("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) "
                      "SELECT sum(x) FROM n")
    with closing(core.connect()) as con:
        with pytest.raises(sqlite3.Error):
            con.execute("DELETE FROM observacoes")
    large = "x" * 10000
    result = core.sql_read("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n "
                           f"WHERE x<1000) SELECT '{large}' AS value FROM n", 1000)
    assert result["truncated"] and result["limit_reason"] == "limite_bytes"
    assert len(result["rows"]) < 200


def test_authorization_and_idempotency(lab):
    proposal = core.proposal("IBGE_PIMPF")["proposta"]
    with pytest.raises(PermissionError):
        core.ingest("IBGE_PIMPF", proposal)
    core.approve("IBGE_PIMPF", proposal, "automated-test-NOT-human")
    with pytest.raises(PermissionError):
        core.approve("IBGE_PIMPF", proposal, "automated-test-NOT-human-duplicate")
    assert core.ingest("IBGE_PIMPF", proposal)["status"] == "ok"
    with pytest.raises((PermissionError, ValueError)):
        core.ingest("IBGE_PIMPF", proposal)
    second = core.proposal("IBGE_PIMPF")["proposta"]
    core.approve("IBGE_PIMPF", second, "automated-test-NOT-human")
    assert core.ingest("IBGE_PIMPF", second)["status"] == "idempotente"
    assert core.sql_read("SELECT count(*) AS n FROM observacoes")["rows"][0]["n"] == 384
    assert core.sql_read("SELECT count(*) AS n FROM cargas")["rows"][0]["n"] == 8
    assert core.sql_read("SELECT * FROM vw_ultima_observacao WHERE codigo_serie='IBGE_PIMPF'")["rows"]
    assert '"tool": "ingerir_serie_cache"' in (lab / "logs/audit.jsonl").read_text()


def test_expired_or_changed_proposal(lab):
    proposal = core.proposal("IBGE_PIMPF")["proposta"]
    core.approve("IBGE_PIMPF", proposal, "automated-test-NOT-human")
    with closing(core.connect(write=True)) as con, con:
        con.execute("UPDATE autorizacoes SET expira_em=?", (time.time() - 1,))
    with pytest.raises(PermissionError):
        core.ingest("IBGE_PIMPF", proposal)
    core.approve("IBGE_PIMPF", proposal, "automated-test-NOT-human-renewal")
    with pytest.raises(ValueError):
        core.ingest("IBGE_PIMPF", "invented-digest")
    assert len(core.sql_read("SELECT * FROM series")["rows"]) == 7


def test_cache_tampering_and_path_rejection(lab):
    path = core.RAW / "IBGE_PIMPF.csv"
    path.write_text(path.read_text() + "2026-01-01,100\n")
    with pytest.raises(ValueError, match="Checksum"):
        core.proposal("IBGE_PIMPF")
    with pytest.raises(ValueError, match="fora do catalogo"):
        core.cache("../../other")
    with pytest.raises(ValueError):
        analytics.validated_manifest("../other")


def test_transaction_rollback_mid_ingest(lab):
    proposal = core.proposal("IBGE_PIMPF")["proposta"]
    core.approve("IBGE_PIMPF", proposal, "automated-test-NOT-human")
    with closing(core.connect(write=True)) as con, con:
        con.execute("CREATE TRIGGER test_fail BEFORE INSERT ON observacoes "
                    "WHEN NEW.codigo_serie='IBGE_PIMPF' AND NEW.data_ref='2023-01-01' "
                    "BEGIN SELECT RAISE(ABORT,'synthetic injected failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="synthetic"):
        core.ingest("IBGE_PIMPF", proposal)
    assert not core.sql_read("SELECT * FROM series WHERE codigo_serie='IBGE_PIMPF'")["rows"]
    assert len(core.sql_read("SELECT * FROM cargas")["rows"]) == 7
    with closing(core.connect()) as con:
        assert con.execute("SELECT consumida FROM autorizacoes").fetchone()[0] == 0


def test_foreign_keys_and_unique_month(lab):
    with closing(core.connect(write=True)) as con, con:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO observacoes VALUES ('UNKNOWN','2025-01-01',1,1)")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO observacoes SELECT * FROM observacoes LIMIT 1")


def test_compounding_official_and_independent_reference(lab):
    monthly, _ = core.series("BCB_433")
    result = analytics.accumulated(monthly)
    reference = json.loads((core.RAW / "reference_ipca_13522.json").read_text())["dados"]
    official = {pd.to_datetime(r["data"], format="%d/%m/%Y").strftime("%Y-%m-%d"):
                float(r["valor"]) for r in reference}
    deviations = [abs(float(r.valor) - official[r.data_ref]) for r in result.itertuples()]
    assert len(deviations) == 37
    assert max(deviations) <= 0.011
    last = monthly.valor.iloc[-12:]
    independent = (math.prod(1 + Decimal(str(x)) / 100 for x in last) - 1) * 100
    assert result.valor.iloc[-1] == pytest.approx(float(independent), abs=1e-10)


def test_full_common_quarters_and_ratio():
    a = synthetic(8, value=100)
    a.loc[3:5, "valor"] = 104
    b = a.iloc[:7]
    result = analytics.quarter_pair({"a": a, "b": b})
    assert result["trimestre_atual"] == "2022Q2"
    assert result["meses"] == [f"2022-{n:02d}-01" for n in range(1, 7)]
    assert result["series"]["a"]["variacao_percentual"] == pytest.approx(4)
    with pytest.raises(ValueError):
        analytics.quarter_pair({"a": a.iloc[2:]})


@pytest.mark.parametrize("adjustment,method", [("sim", "STL"), ("unknown", "STL"), ("nao", "X-13")])
def test_seasonal_no_silent_fallback(adjustment, method):
    with pytest.raises(ValueError):
        analytics.seasonal(synthetic(), adjustment, method)


def test_artifacts_docx_numerical_consistency_and_tamper(lab):
    database_before = core.digest(core.DB)
    inf = analytics.inflation()
    act = analytics.activity()
    result = reports.render()
    assert inf["pontos"] == 36
    assert inf["inicio"] == "2023-01-01"
    assert act["trimestre_atual"] == "2025Q4"
    with Image.open(core.OUT / "inflacao/grafico.png") as image:
        image.verify()
    with zipfile.ZipFile(result["docx"]) as z:
        assert z.testzip() is None
    docx = "\n".join(p.text for p in Document(result["docx"]).paragraphs)
    markdown = (core.OUT / "nota_conjuntura.md").read_text()
    numbers = result["numeros_conferidos"]
    for text in (reports.DRAFT, *(f"{v:.4f}" for v in numbers.values())):
        assert text in docx and text in markdown
    assert "VAR" not in markdown
    assert core.digest(core.DB) == database_before
    for kind in ("inflacao", "atividade"):
        assert analytics.validated_manifest(kind)
    path = core.OUT / "inflacao/tabela.csv"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="alterado"):
        reports.render()


def test_reset_preserves_outputs_logs_and_initial_state(lab):
    core.OUT.mkdir()
    sentinel = core.OUT / "keep.txt"
    sentinel.write_text("test evidence")
    core.reset()
    assert sentinel.read_text() == "test evidence"
    assert len(core.sql_read("SELECT * FROM series")["rows"]) == 7
    assert (lab / "logs/audit.jsonl").is_file()
    with closing(sqlite3.connect(lab / "data/econ_lab_backup.db")) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT COUNT(*) FROM series").fetchone()[0] == 7


def test_authorization_bound_to_database(lab, monkeypatch):
    proposed = core.proposal("IBGE_PIMPF")["proposta"]
    other = lab / "data/isolated.db"
    with closing(core.connect()) as source, closing(sqlite3.connect(other)) as target:
        source.backup(target)
    monkeypatch.setattr(core, "DB", other)
    assert core.proposal("IBGE_PIMPF")["proposta"] != proposed
    with pytest.raises(ValueError):
        core.approve("IBGE_PIMPF", proposed, "automated-test-NOT-human")


def test_human_authorization_cli_rejects_pipe(lab):
    proposed = core.proposal("IBGE_PIMPF")["proposta"]
    result = subprocess.run(
        [sys.executable, "-m", "econlab.cli", "authorize", "IBGE_PIMPF", proposed,
         "--actor", "synthetic-operator-NOT-human"],
        input=f"AUTORIZAR {proposed}\n", text=True, capture_output=True,
        env={**os.environ, "ECONLAB_ROOT": str(lab)}, timeout=30, check=False)
    assert result.returncode != 0 and "terminal interativo" in result.stderr
    with closing(core.connect()) as con:
        assert con.execute("SELECT COUNT(*) FROM autorizacoes").fetchone()[0] == 0


def test_metadata_provenance_tampering(lab):
    path = core.RAW / "IBGE_PMC.metadata.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="evidencia metadata"):
        core.cache("IBGE_PMC")


def test_changed_cache_not_silently_overwritten(lab):
    path = core.RAW / "BCB_433.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "valor"] += 0.1
    frame.to_csv(path, index=False)
    meta = core.catalog()
    meta["BCB_433"]["sha256"] = core.digest(path)
    (core.RAW / "catalog.json").write_text(json.dumps(meta))
    proposal = core.proposal("BCB_433")["proposta"]
    core.approve("BCB_433", proposal, "automated-test-NOT-human")
    with pytest.raises(ValueError, match="revisado"):
        core.ingest("BCB_433", proposal)
    assert core.series("BCB_433")[0].valor.iloc[0] != frame.valor.iloc[0]


def test_all_mcp_servers_real_stdio(lab):
    async def exercise():
        expected = {
            "sqlite-econ": {"listar_series", "obter_serie", "descrever_esquema", "consulta_sql"},
            "series-publicas": {"status_cache", "ingerir_serie_cache"},
            "analytics": {"acumulado_12m", "comparacao_trimestral", "ajuste_sazonal", "resultados_validados"},
            "relatorios": {"listar_templates", "renderizar_relatorio"},
        }
        for name, names in expected.items():
            params = StdioServerParameters(command=sys.executable,
                args=["-m", "econlab.server", name], env={**os.environ, "ECONLAB_ROOT": str(lab)})
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    tools = await client.list_tools()
                    assert {t.name for t in tools.tools} == names
                    for tool in tools.tools:
                        assert tool.inputSchema["type"] == "object"
                        assert tool.outputSchema["type"] == "object"
                    if name == "sqlite-econ":
                        result = await client.call_tool("listar_series", {})
                        assert not result.isError and len(result.structuredContent["rows"]) == 7
                        result = await client.call_tool("consulta_sql", {"sql": "DROP TABLE observacoes"})
                        assert result.isError
                    elif name == "series-publicas":
                        result = await client.call_tool("status_cache", {})
                        assert not result.isError and result.structuredContent["linhas"] == 48
                    elif name == "analytics":
                        for tool in ("acumulado_12m", "comparacao_trimestral"):
                            assert not (await client.call_tool(tool, {})).isError
                    else:
                        assert not (await client.call_tool("renderizar_relatorio", {})).isError
    asyncio.run(exercise())


def test_customization_tool_identifiers_and_files():
    from econlab.server import make_server
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]

    async def inventory():
        return {name: {tool.name for tool in await make_server(name).list_tools()}
                for name in ("sqlite-econ", "series-publicas", "analytics", "relatorios")}

    available = asyncio.run(inventory())
    paths = list((root / ".github/agents").glob("*.agent.md"))
    assert len(paths) == 4
    paths += list((root / ".github/prompts").glob("*.prompt.md"))
    assert len(paths) == 6
    for path in paths:
        header = path.read_text().split("---", 2)[1]
        line = next(line for line in header.splitlines() if line.startswith("tools:"))
        tools = ast.literal_eval(line.split(":", 1)[1].strip())
        assert all("/" in tool for tool in tools)
        for tool in tools:
            server, name = tool.split("/", 1)
            assert server in available
            assert name == "*" or name in available[server]
    assert len(list((root / ".github/skills").glob("*/SKILL.md"))) == 3
    vscode = json.loads((root / ".vscode/mcp.json").read_text())
    portable = json.loads((root / ".mcp.json").read_text())
    assert set(vscode["servers"]) == set(portable["mcpServers"]) == set(available)


def test_all_72_inflation_table_cells_independently(lab):
    analytics.inflation()
    table = pd.read_csv(core.OUT / "inflacao/tabela.csv")
    checked = 0
    for code in ("BCB_433", "BCB_189"):
        raw = pd.read_csv(core.RAW / f"{code}.csv")
        for row in table.itertuples():
            end = raw.index[raw.data_ref == row.data_ref][0]
            window = raw.valor.iloc[end-11:end+1]
            independent = (math.prod(1 + Decimal(str(x)) / 100 for x in window) - 1) * 100
            assert getattr(row, code) == pytest.approx(float(independent), abs=1e-8)
            checked += 1
    assert checked == 72
