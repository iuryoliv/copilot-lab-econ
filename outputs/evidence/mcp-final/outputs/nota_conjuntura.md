# Nota de conjuntura: inflacao e atividade

Rascunho — requer revisão do economista responsável

## Destaque

Em 2025-12-01, o IPCA acumulado em 12 meses foi 4.2644% e o IGP-M, -1.0422%. Fonte: BCB/SGS 433 e 189.

## Contexto

Exercicio historico com janela congelada de janeiro/2022 a dezembro/2025. Nao representa a conjuntura corrente de 2026 nem uma projecao oficial.

## Inflacao

Acumulados compostos, calculados por codigo deterministico; 36 pontos mensais. As taxas mensais nao foram somadas. Tabela: inflacao/tabela.csv; grafico: inflacao/grafico.png.

## Atividade

Periodo comum: 2025Q4 contra 2025Q3. Razao das medias trimestrais menos um: PMC (STL) 0.4039%; IBC-Br (ajuste oficial) 0.4009%. Fontes: IBGE/SIDRA 8880 e BCB/SGS 24364.

Seis meses usados: 2025-07-01, 2025-08-01, 2025-09-01, 2025-10-01, 2025-11-01, 2025-12-01. Tabela: atividade/trimestres.csv. Niveis de indices com bases distintas nao sao comparados.

## Riscos e limitacoes

STL ilustrativo, nao equivale ao X-13 nem ao ajuste oficial IBGE. Estimativas de ponta e revisoes dependem da amostra 2022-2025. Indices com bases distintas: comparar variacoes, nao niveis.

Dados publicos podem ser revisados. A amostra congelada limita inferencias. Nao ha recomendacao de investimento. Revisao humana numerica e editorial obrigatoria.

## Fontes e rastreabilidade

- BCB_433: IPCA - variacao mensal; unidade % a.m.; ajuste de origem nao; extracao UTC 2026-10-29T19:58:53.327262+00:00; referencias 2022-01-01 a 2025-12-01; SHA256 df47e49e2e92154f8ecfcedcf96c53e48cbab4a2b6613094ca752b8c9bf31401; URL https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/2022&dataFinal=31/12/2025; metadados https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.paint?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=433.

- BCB_189: IGP-M - variacao mensal; unidade % a.m.; ajuste de origem nao; extracao UTC 2026-10-29T19:58:53.240097+00:00; referencias 2022-01-01 a 2025-12-01; SHA256 34af9eec25a5dae7f74dbe102e07aaff0f2540208e8c0315893273a692a9dcbf; URL https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados?formato=json&dataInicial=01/01/2022&dataFinal=31/12/2025; metadados https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.paint?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=189.

- IBGE_PMC: PMC - Índice de volume de vendas no comércio varejista; unidade indice (2022=100); ajuste de origem nao; extracao UTC 2026-10-29T19:58:54.110576+00:00; referencias 2022-01-01 a 2025-12-01; SHA256 12828af100c2ae41d247d355927a6dfbb124ffb6bdd92cb40a072b8cdd4b5a6f; URL https://apisidra.ibge.gov.br/values/t/8880/n1/1/v/7169/p/202201,202202,202203,202204,202205,202206,202207,202208,202209,202210,202211,202212,202301,202302,202303,202304,202305,202306,202307,202308,202309,202310,202311,202312,202401,202402,202403,202404,202405,202406,202407,202408,202409,202410,202411,202412,202501,202502,202503,202504,202505,202506,202507,202508,202509,202510,202511,202512/c11046/56734?formato=json; metadados https://servicodados.ibge.gov.br/api/v3/agregados/8880/metadados.

- BCB_24364: IBC-Br com ajuste sazonal; unidade indice; ajuste de origem sim; extracao UTC 2026-10-29T19:58:55.383947+00:00; referencias 2022-01-01 a 2025-12-01; SHA256 d0d124e2f6e422ff798b2704688b1e0e50688b3b7b6d0cbe1b7fa3abc59c6ffb; URL https://api.bcb.gov.br/dados/serie/bcdata.sgs.24364/dados?formato=json&dataInicial=01/01/2022&dataFinal=31/12/2025; metadados https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.paint?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=24364.

## Artefatos de passagem entre agentes

inflacao/manifest.json e atividade/manifest.json, tabelas e PNG com hashes verificados. O redator nao presume memoria de outro chat.
