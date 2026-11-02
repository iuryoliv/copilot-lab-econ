from __future__ import annotations

from docx import Document
from docx.shared import Inches

from econlab import analytics, core

DRAFT = "Rascunho — requer revisão do economista responsável"


def render() -> dict:
    inflation = analytics.validated_manifest("inflacao")
    activity = analytics.validated_manifest("atividade")
    ipca, igpm = inflation["ultimo"]["BCB_433"], inflation["ultimo"]["BCB_189"]
    pmc = activity["series"]["PMC_STL"]["variacao_percentual"]
    ibc = activity["series"]["BCB_24364"]["variacao_percentual"]
    text = [
        "# Nota de conjuntura: inflacao e atividade",
        DRAFT,
        "## Destaque",
        f"Em {inflation['fim']}, o IPCA acumulado em 12 meses foi {ipca:.4f}% "
        f"e o IGP-M, {igpm:.4f}%. Fonte: BCB/SGS 433 e 189.",
        "## Contexto",
        "Exercicio historico com janela congelada de janeiro/2022 a dezembro/2025. "
        "Nao representa a conjuntura corrente de 2026 nem uma projecao oficial.",
        "## Inflacao",
        "Acumulados compostos, calculados por codigo deterministico; 36 pontos mensais. "
        "As taxas mensais nao foram somadas. Tabela: inflacao/tabela.csv; grafico: inflacao/grafico.png.",
        "## Atividade",
        f"Periodo comum: {activity['trimestre_atual']} contra {activity['trimestre_anterior']}. "
        f"Razao das medias trimestrais menos um: PMC (STL) {pmc:.4f}%; "
        f"IBC-Br (ajuste oficial) {ibc:.4f}%. Fontes: IBGE/SIDRA 8880 e BCB/SGS 24364.",
        f"Seis meses usados: {', '.join(activity['meses'])}. "
        "Tabela: atividade/trimestres.csv. Niveis de indices com bases distintas nao sao comparados.",
        "## Riscos e limitacoes",
        activity["limitacoes"],
        "Dados publicos podem ser revisados. A amostra congelada limita inferencias. "
        "Nao ha recomendacao de investimento. Revisao humana numerica e editorial obrigatoria.",
        "## Fontes e rastreabilidade",
    ]
    sources = {**inflation["fontes"], **activity["fontes"]}
    for code, meta in sources.items():
        text.append(f"- {code}: {meta['nome']}; unidade {meta['unidade']}; "
                    f"ajuste de origem {meta['ajuste_sazonal']}; "
                    f"extracao UTC {meta['extraido_em']}; "
                    f"referencias {meta['inicio']} a {meta['fim']}; "
                    f"SHA256 {meta['sha256']}; URL {meta['url']}; "
                    f"metadados {meta['metadata_url']}.")
    text += ["## Artefatos de passagem entre agentes",
             "inflacao/manifest.json e atividade/manifest.json, tabelas e PNG com hashes "
             "verificados. O redator nao presume memoria de outro chat."]
    core.OUT.mkdir(parents=True, exist_ok=True)
    md, docx = core.OUT / "nota_conjuntura.md", core.OUT / "nota_conjuntura.docx"
    md.write_text("\n\n".join(text) + "\n", encoding="utf-8")
    document = Document()
    for paragraph in text:
        if paragraph.startswith("# "):
            document.add_heading(paragraph[2:], 0)
        elif paragraph.startswith("## "):
            document.add_heading(paragraph[3:], 1)
        else:
            document.add_paragraph(paragraph)
    document.add_picture(str(core.OUT / "inflacao/grafico.png"), width=Inches(6))
    document.save(docx)
    reopened = Document(docx)
    reopened_text = "\n".join(p.text for p in reopened.paragraphs)
    for required in (DRAFT, f"{ipca:.4f}", f"{igpm:.4f}", f"{pmc:.4f}", f"{ibc:.4f}"):
        if required not in reopened_text or required not in md.read_text(encoding="utf-8"):
            raise ValueError("DOCX/Markdown nao preservam numeros ou marca de revisao.")
    result = {"markdown": str(md), "docx": str(docx), "status": DRAFT,
              "sha256": {p.name: core.digest(p) for p in (md, docx)},
              "numeros_conferidos": {"IPCA": ipca, "IGPM": igpm, "PMC": pmc, "IBC": ibc}}
    analytics.save_json(core.OUT / "relatorio_manifest.json", result)
    core.audit("renderizar_relatorio", "ok", **result)
    return result
