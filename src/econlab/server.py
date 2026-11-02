from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from econlab import analytics, core, reports

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True)


def make_server(name: str) -> FastMCP:
    mcp = FastMCP(name)
    if name == "sqlite-econ":
        @mcp.tool(annotations=READ)
        def listar_series() -> dict[str, Any]:
            """Catalogo carregado e ultimas observacoes; nao altera a base."""
            return core.sql_read("SELECT s.*,u.data_ref,u.valor FROM series s JOIN "
                                 "vw_ultima_observacao u USING(codigo_serie) ORDER BY codigo_serie")

        @mcp.tool(annotations=READ)
        def obter_serie(codigo: str, inicio: str = "2022-01-01",
                       fim: str = "2025-12-01") -> dict[str, Any]:
            """Le serie ordenada, com fonte, unidade, ajuste e extracao."""
            df, meta = core.series(codigo)
            for value in (inicio, fim):
                from datetime import date
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError("Data ISO invalida.")
            if inicio > fim:
                raise ValueError("Inicio posterior ao fim.")
            result = df[(df.data_ref >= inicio) & (df.data_ref <= fim)]
            core.audit("obter_serie", "ok", codigo=codigo, linhas=len(result))
            return {"metadados": meta, "observacoes": result.to_dict("records")}

        @mcp.tool(annotations=READ)
        def descrever_esquema() -> dict[str, Any]:
            """Schema real, excluida a tabela administrativa de autorizacoes."""
            return core.sql_read("SELECT name,sql FROM sqlite_master WHERE "
                                 "name NOT LIKE 'sqlite_%' AND name != 'autorizacoes'")

        @mcp.tool(annotations=READ)
        def consulta_sql(sql: str, limite: int = 1000) -> dict[str, Any]:
            """SELECT limitado; SQLite read-only, authorizer, quotas e deadline."""
            return core.sql_read(sql, limite)

    elif name == "series-publicas":
        @mcp.tool(annotations=READ)
        def status_cache(codigo: str = "IBGE_PIMPF") -> dict[str, Any]:
            """Valida cache e propoe carga sem gravar; retorna digest para autorizacao."""
            result = core.proposal(codigo)
            core.audit("status_cache", "ok", codigo=codigo, proposta=result["proposta"])
            return result

        @mcp.tool(annotations=WRITE)
        def ingerir_serie_cache(codigo: str, proposta: str) -> dict[str, Any]:
            """Grava somente proposta autorizada externamente, vigente e nao consumida."""
            return core.ingest(codigo, proposta)

    elif name == "analytics":
        @mcp.tool(annotations=WRITE)
        def acumulado_12m() -> dict[str, Any]:
            """Calcula 36 pontos IPCA/IGP-M, tabela CSV e PNG em outputs/inflacao."""
            return analytics.inflation()

        @mcp.tool(annotations=WRITE)
        def comparacao_trimestral(metodo: str = "STL") -> dict[str, Any]:
            """PMC STL explicito versus IBC-Br oficial; seis meses comuns completos."""
            return analytics.activity(metodo)

        @mcp.tool(annotations=WRITE)
        def ajuste_sazonal(metodo: str = "STL") -> dict[str, Any]:
            """Executa STL e comparacao; rejeita X-13, sem fallback silencioso."""
            return analytics.activity(metodo)

        @mcp.tool(annotations=READ)
        def resultados_validados(tipo: str) -> dict[str, Any]:
            """Verifica hashes, tabelas, numeros e versao da fonte para passagem de agente."""
            return analytics.validated_manifest(tipo)

    elif name == "relatorios":
        @mcp.tool(annotations=READ)
        def listar_templates() -> dict[str, Any]:
            """Template unico revisavel; sem secao de modelagem nao executada."""
            return {"templates": ["nota-conjuntura"], "marca": reports.DRAFT,
                    "entradas": ["outputs/inflacao/manifest.json", "outputs/atividade/manifest.json"]}

        @mcp.tool(annotations=WRITE)
        def renderizar_relatorio(template: str = "nota-conjuntura") -> dict[str, Any]:
            """Valida artefatos fornecidos e exporta Markdown/DOCX; nao altera dados."""
            if template != "nota-conjuntura":
                raise ValueError("Template desconhecido.")
            return reports.render()
    else:
        raise ValueError(f"Servidor desconhecido: {name}")
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("server", choices=["sqlite-econ", "series-publicas", "analytics", "relatorios"])
    args = parser.parse_args()
    make_server(args.server).run(transport="stdio")


if __name__ == "__main__":
    main()
