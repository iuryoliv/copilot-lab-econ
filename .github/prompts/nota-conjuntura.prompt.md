---
name: nota-conjuntura
description: Renderiza nota historica revisavel com passagem explicita de artefatos.
agent: redator-relatorios
tools: ['analytics/resultados_validados', 'relatorios/*']
---

Use a skill nota-conjuntura. Entradas explicitamente fornecidas:
outputs/inflacao/manifest.json, outputs/inflacao/tabela.csv,
outputs/inflacao/grafico.png, outputs/atividade/manifest.json,
outputs/atividade/trimestres.csv e outputs/atividade/pmc_stl.csv.
Valide pelos tools analytics/resultados_validados antes de renderizar.
Redija sobre 2025Q4 contra 2025Q3, janela historica e nao conjuntura atual.
Exporte outputs/nota_conjuntura.md e outputs/nota_conjuntura.docx.
Preserve fontes, extracao, limitacoes STL e marca de revisao; sem recomendacoes
de investimento e sem VAR nao executado.
