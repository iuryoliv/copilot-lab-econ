"""Runs the actual authenticated Copilot CLI, not an SDK simulation or subagent."""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

from econlab import analytics, core


def client(work: Path, phase: str, agent: str, prompt: str,
           approvals: list[str], disabled: list[str]) -> dict:
    config = json.loads((Path(__file__).resolve().parents[1] / ".mcp.json").read_text())
    for server in config["mcpServers"].values():
        server["command"] = str(Path(__file__).resolve().parents[1] / ".venv/bin/python")
        server["env"] = {"ECONLAB_ROOT": str(work)}
    config_path = work / "mcp-client.json"
    analytics.save_json(config_path, config)
    args = ["copilot", "--agent", agent, "--disable-builtin-mcps",
            "--additional-mcp-config", f"@{config_path}", "--deny-tool=shell",
            "--deny-tool=write", "--excluded-tools=sql", "--no-remote-export",
            "--output-format=json", "-p", prompt]
    args.extend(f"--allow-tool={tool}" for tool in approvals)
    args.extend(f"--disable-mcp-server={server}" for server in disabled)
    completed = subprocess.run(args, cwd=Path(__file__).resolve().parents[1],
                               text=True, capture_output=True, timeout=240, check=False)
    (work / f"{phase}.jsonl").write_text(completed.stdout, encoding="utf-8")
    (work / f"{phase}.stderr").write_text(completed.stderr, encoding="utf-8")
    events = []
    for line in completed.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    result = next((e for e in events if e.get("type") == "result"), {})
    calls = [e["data"] for e in events if e.get("type") == "tool.execution_start"]
    finishes = [e["data"] for e in events if e.get("type") == "tool.execution_complete"]
    inventory = []
    for e in events:
        if e.get("type") == "session.usage_checkpoint":
            for state in e["data"].get("promptCacheBreakState", []):
                for model in state.get("models", {}).values():
                    inventory.extend(t["name"] for t in model.get("tools", []))
    summary = {"phase": phase, "agent": agent, "session_id": result.get("sessionId"),
               "process_exit": completed.returncode, "result_exit": result.get("exitCode"),
               "calls": [{"name": c["toolName"], "server": c.get("mcpServerName"),
                          "transport": c.get("mcpTransport"), "args": c.get("arguments")}
                         for c in calls],
               "completions": [{"id": c["toolCallId"], "success": c.get("success")}
                               for c in finishes],
               "exposed_tools": sorted(set(inventory)),
               "answer": [e["data"].get("content", "") for e in events
                          if e.get("type") == "assistant.message" and e["data"].get("content")]}
    analytics.save_json(work / f"{phase}-summary.json", summary)
    if completed.returncode or result.get("exitCode") != 0:
        raise RuntimeError(f"Cliente bloqueado/falhou; inspecione {work / (phase + '.stderr')} "
                           "e transcript. Nao contornar confianca/autenticacao.")
    if not any(c.get("mcpTransport") == "stdio" for c in calls):
        raise AssertionError(f"{phase}: sem chamada MCP stdio real; nao validado.")
    if any(c.get("success") is False for c in finishes):
        raise AssertionError(f"{phase}: ferramenta falhou; conferir transcript.")
    forbidden = {"bash", "apply_patch", "task", "web_fetch", "sql"}
    if forbidden.intersection(inventory):
        raise AssertionError(f"{phase}: ferramentas fora do menor privilegio: {inventory}")
    return summary


def execute(work: Path, disabled: list[str]) -> dict:
    if work.exists():
        raise FileExistsError(f"Ensaio ja existe: {work}; escolha outro --run.")
    work.mkdir(parents=True)
    shutil.copytree(core.RAW, work / "data/raw")
    with closing(core.connect()) as source, closing(sqlite3.connect(work / "data/econ_lab.db")) as target:
        source.backup(target)
    original = core.ROOT, core.DB, core.RAW, core.OUT
    core.ROOT, core.DB, core.RAW, core.OUT = work, work / "data/econ_lab.db", work / "data/raw", work / "outputs"
    stages = []
    try:
        proposed = core.proposal("IBGE_PIMPF")
        stages.append(client(work, "01-proposta", "engenheiro-dados",
            "Use realmente sqlite-econ/listar_series e series-publicas/status_cache para IBGE_PIMPF. "
            "Nao ingira nem autorize. Mostre sete series e proposta do cache, 48 meses. "
            "Sem terminal, sem delegacao, sem simular.",
            ["sqlite-econ", "series-publicas(status_cache)"], disabled))
        authorization = core.approve("IBGE_PIMPF", proposed["proposta"],
                                     "automated-rehearsal-NOT-human")
        analytics.save_json(work / "authorization.json",
                            {**authorization, "human_approval": False, "scope": str(core.DB)})
        stages.append(client(work, "02-ingestao", "engenheiro-dados",
            "Ensaio automatizado somente na copia isolada indicada pelas ferramentas, nao na base de demo. "
            "O harness externo registrou autorizacao automatizada, NAO humana, ator "
            f"automated-rehearsal-NOT-human, proposta {proposed['proposta']}. "
            "Nao diga que houve confirmacao humana. Nao conceda autorizacao por conta propria. "
            "Execute series-publicas/ingerir_serie_cache para IBGE_PIMPF com esse digest e "
            "confira 48 observacoes e oito series usando sqlite-econ/consulta_sql. "
            "Sem terminal ou delegacao.",
            ["sqlite-econ", "series-publicas"], disabled))
        if len(core.sql_read("SELECT * FROM series")["rows"]) != 8:
            raise AssertionError("Copilot nao realizou a ingestao na copia.")
        stages.append(client(work, "03-analise", "analista-macro",
            "Execute o laboratorio real pelos MCP locais. Use explicitamente as skills "
            "graficos-padrao e dessazonalizacao. Chame analytics/acumulado_12m para obter "
            "36 pontos IPCA e IGP-M (ultimos tres anos da amostra 2022-2025) e PNG. "
            "Chame analytics/comparacao_trimestral com metodo STL, PMC versus IBC-Br oficial. "
            "Confira ambos com resultados_validados. Informe numeros, seis meses, fontes, "
            "extracao, caminhos dos dois manifestos e limitacoes STL. Sem terminal, ingestao "
            "ou delegacao. Nao chame isso de conjuntura corrente de 2026.",
            ["sqlite-econ", "analytics"], disabled))
        for kind in ("inflacao", "atividade"):
            analytics.validated_manifest(kind)
        stages.append(client(work, "04-econometria", "econometrista",
            "Confira os metadados de BCB_24364 e IBGE_PMC com obter_serie. "
            "Consulte analytics/resultados_validados tipo atividade e explique por que nao "
            "reajustar IBC-Br e por que STL nao equivale a X-13. Nao executar VAR ou terminal. "
            "Use os resultados ja produzidos; nao suponha memoria de outra conversa.",
            ["sqlite-econ", "analytics(resultados_validados)"], disabled))
        stages.append(client(work, "05-nota", "redator-relatorios",
            f"Use a skill nota-conjuntura. Entradas explicitamente fornecidas desta copia: "
            f"{work}/outputs/inflacao/manifest.json, tabela.csv e grafico.png nessa pasta; "
            f"{work}/outputs/atividade/manifest.json, trimestres.csv e pmc_stl.csv nessa pasta. "
            "Chame analytics/resultados_validados para inflacao e atividade, listar_templates "
            "e renderizar_relatorio. Exporte Markdown e DOCX revisaveis, janela historica, "
            "sem VAR, sem recomendacao de investimento, com fontes, extracao, limitacoes STL "
            "e marca Rascunho — requer revisão do economista responsável. "
            "Nao use terminal nem delegacao, nao calcule numeros no texto.",
            ["analytics(resultados_validados)", "relatorios"], disabled))
        if not (core.OUT / "nota_conjuntura.docx").is_file():
            raise AssertionError("Copilot nao gerou DOCX.")
        final = {"executor": "GitHub Copilot CLI real autenticado",
                 "version": subprocess.check_output(["copilot", "--version"], text=True).splitlines()[0],
                 "human_approval": False, "authorization": authorization,
                 "scope": "copia isolada de ensaio; base da demo permanece com sete series",
                 "vscode_ui_validated": False, "stages": stages,
                 "outputs": str(core.OUT), "finished_at": core.now()}
        analytics.save_json(work / "evidence.json", final)
        return {"client": final["executor"], "stages": len(stages), "outputs": str(core.OUT),
                "human_approval": False, "evidence": str(work / "evidence.json")}
    finally:
        core.ROOT, core.DB, core.RAW, core.OUT = original


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="copilot-e2e")
    parser.add_argument("--disable-server", action="append", default=[
        "articles", "azure", "computer-use", "se-automation-crm"])
    args = parser.parse_args()
    if not args.run.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Nome de ensaio simples, sem caminhos.")
    print(json.dumps(execute(core.OUT / "evidence" / args.run, args.disable_server),
                     ensure_ascii=False, indent=2))
