"""Independent read-only verification of public values, documents and real CLI evidence."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import zipfile
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import pandas as pd
from docx import Document
from PIL import Image

from econlab import analytics, core, reports


def verify(run: str) -> dict:
    work = core.OUT / "evidence" / run
    evidence = json.loads((work / "evidence.json").read_text(encoding="utf-8"))
    if evidence["executor"] != "GitHub Copilot CLI real autenticado":
        raise ValueError("O ensaio selecionado nao e execucao CLI real.")
    independent = {}
    source_db = work / "data/econ_lab.db"
    with closing(sqlite3.connect(f"{source_db.as_uri()}?mode=ro", uri=True)) as con:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert con.execute("SELECT COUNT(*) FROM series").fetchone()[0] == 8
        assert con.execute("SELECT COUNT(*) FROM observacoes").fetchone()[0] == 384
        rows = con.execute("SELECT data_ref,valor FROM observacoes WHERE codigo_serie='BCB_433' "
                           "ORDER BY data_ref").fetchall()
    official = json.loads((work / "data/raw/reference_ipca_13522.json").read_text())["dados"]
    reference = {pd.to_datetime(r["data"], format="%d/%m/%Y").strftime("%Y-%m-%d"):
                 Decimal(r["valor"]) for r in official}
    differences = []
    for index in range(11, len(rows)):
        value = (math.prod(1 + Decimal(str(v)) / 100 for _, v in rows[index-11:index+1]) - 1) * 100
        differences.append(abs(value - reference[rows[index][0]]))
    assert len(differences) == 37 and max(differences) <= Decimal("0.011")
    independent["ipca_vs_13522"] = {"pontos": len(differences), "max_desvio_pp": float(max(differences)),
                                   "tolerancia_pp": 0.011}
    out = work / "outputs"
    for kind in ("inflacao", "atividade"):
        manifest = json.loads((out / kind / "manifest.json").read_text())
        for name, sha in manifest["artefatos"].items():
            assert core.digest(out / kind / name) == sha
    table = pd.read_csv(out / "inflacao/tabela.csv")
    assert len(table) == 36 and table.data_ref.iloc[-1] == "2025-12-01"
    compared = 0
    for code in ("BCB_433", "BCB_189"):
        raw = pd.read_csv(work / f"data/raw/{code}.csv")
        for row in table.itertuples():
            end = raw.index[raw.data_ref == row.data_ref][0]
            window = raw.valor.iloc[end-11:end+1]
            rate = 100 * (math.prod(1 + Decimal(str(x)) / 100 for x in window) - 1)
            assert abs(float(rate) - float(getattr(row, code))) < 1e-8
            compared += 1
    independent["inflacao_csv"] = {"celulas_conferidas_decimal": compared, "tolerancia_pp": 1e-8}
    quarter = pd.read_csv(out / "atividade/trimestres.csv")
    activity = json.loads((out / "atividade/manifest.json").read_text())
    assert quarter.data_ref.tolist() == [f"2025-{n:02d}-01" for n in range(7, 13)]
    independent["atividade"] = {}
    for code in ("PMC_STL", "BCB_24364"):
        numbers = [Decimal(str(x)) for x in quarter[code]]
        rate = 100 * (sum(numbers[3:]) / sum(numbers[:3]) - 1)
        assert abs(float(rate) - activity["series"][code]["variacao_percentual"]) < 1e-8
        independent["atividade"][code] = float(rate)
    with Image.open(out / "inflacao/grafico.png") as image:
        size = image.size
        image.verify()
    with zipfile.ZipFile(out / "nota_conjuntura.docx") as archive:
        assert archive.testzip() is None
    docx = "\n".join(p.text for p in Document(out / "nota_conjuntura.docx").paragraphs)
    md = (out / "nota_conjuntura.md").read_text()
    for text in (reports.DRAFT, "4.2644", "-1.0422", "0.4039", "0.4009"):
        assert text in docx and text in md
    assert "VAR" not in md
    calls = [c for stage in evidence["stages"] for c in stage["calls"]]
    successful = [c for stage in evidence["stages"] for c in stage["completions"]]
    assert all(c["success"] for c in successful)
    assert {c["server"] for c in calls if c.get("server")} == {
        "sqlite-econ", "series-publicas", "analytics", "relatorios"}
    skills = {c["args"]["skill"] for c in calls if c["name"] == "skill"}
    assert skills == {"graficos-padrao", "dessazonalizacao", "nota-conjuntura"}
    forbidden = {"bash", "apply_patch", "task", "web_fetch", "sql"}
    assert all(not forbidden.intersection(stage["exposed_tools"]) for stage in evidence["stages"])
    assert not evidence["human_approval"]
    with closing(core.connect()) as con:
        assert con.execute("SELECT COUNT(*) FROM series").fetchone()[0] == 7
        assert con.execute("SELECT COUNT(*) FROM observacoes WHERE codigo_serie='IBGE_PIMPF'").fetchone()[0] == 0
    result = {"verified_at": core.now(), "run": run, "executor": evidence["executor"],
              "mcp_calls_from_copilot": sum(bool(c.get("server")) for c in calls),
              "stages": len(evidence["stages"]), "skills": sorted(skills),
              "human_approval": False, "vscode_ui_validated": False,
              "main_demo_series": 7, "pimpf_only_in_cache_main_demo": True,
              "independent_reference": independent, "png_size": list(size),
              "docx_zip_and_text": "ok", "numbers_checked": 4,
              "outputs": str(out)}
    analytics.save_json(work / "verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="copilot-final")
    args = parser.parse_args()
    if not args.run.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Nome de ensaio simples.")
    print(json.dumps(verify(args.run), ensure_ascii=False, indent=2))
