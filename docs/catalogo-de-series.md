# Catalogo de series publicas

Amostra congelada **2022-01-01 a 2025-12-01**, 48 meses continuos por serie.
Extracao efetiva em **2026-10-29 UTC**; instante exato por serie, URL completa,
hash do CSV, resposta original e metadados em `data/raw/catalog.json`.
Os CSVs nao sao sinteticos. Fixtures sinteticas aparecem somente nos testes,
explicitamente rotuladas. Nenhum dado foi fabricado para cobrir indisponibilidade.

| Codigo | Conteudo | Unidade operacional | Ajuste de origem |
|---|---|---|---|
| BCB_433 | IPCA mensal, origem IBGE, distribuido pelo SGS | % a.m. | nao |
| BCB_189 | IGP-M mensal, origem FGV, distribuido pelo SGS | % a.m. | nao |
| BCB_4189 | Selic acumulada no mes anualizada, base 252 | % a.a. | nao aplicavel |
| BCB_3698 | Dolar americano venda, media do periodo mensal | R$/US$ na amostra | nao aplicavel |
| BCB_24363 | IBC-Br sem ajuste sazonal | indice | nao |
| BCB_24364 | IBC-Br com ajuste sazonal oficial | indice | sim |
| IBGE_PMC | Volume de vendas do comercio varejista, Brasil | indice 2022=100 | nao |
| IBGE_PIMPF | Producao fisica, industria geral, Brasil | indice 2022=100 | nao |

O titulo oficial de SGS 3698 e **Exchange rate - Free - United States dollar
(sale) - period average - 3698**, unidade **c.m.u./US$**. Na amostra pos-1994,
equivale a R$/US$. Nao rotular sem ressalva toda a historia desde 1953 como
reais nem adicionar "PTAX" como se constasse nesse titulo oficial.
SGS 4189 nao e a meta Selic nem a taxa mensal nao anualizada.

## Fontes BCB: verificacao efetiva

Valores: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.CODIGO/dados`,
com `formato=json`, `dataInicial=01/01/2022`, `dataFinal=31/12/2025`.
Normalizar a ordenacao; endpoints de ultimos valores podem vir decrescentes.

Metadados: selecionar a serie pela rota oficial
`https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.paint?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=CODIGO`,
depois ler **na mesma sessao HTTP**
`https://www3.bcb.gov.br/sgspub/JSP/consultarmetadados/cmiDadosBasicos.jsp`.
Foram conferidos codigo, titulo, periodicidade mensal e unidade de todas as seis.
O texto oficial salvo em `BCB_CODIGO.metadata.json` documenta o resultado.
O CKAN nao possui entradas identificaveis para todas essas series: nao usar
busca vazia no CKAN como prova de inexistencia dos dados SGS.

Referencia independente do IPCA composto: SGS **13522**, armazenada em
`reference_ipca_13522.json`, 37 pontos de dezembro/2022 a dezembro/2025.
Nao e uma nona serie carregada na base da demonstracao.

## Selecoes SIDRA efetivamente validadas

| Pesquisa | Tabela | Variavel | Classificacao | Categoria | Territorio |
|---|---:|---:|---:|---:|---|
| PMC, volume sem ajuste | 8880 | 7169 | 11046 | 56734 | N1/1 Brasil |
| PIM-PF, industria geral sem ajuste | 8888 | 12606 | 544 | 129314 | N1/1 Brasil |

Metadados oficiais:
[PMC](https://servicodados.ibge.gov.br/api/v3/agregados/8880/metadados) e
[PIM-PF](https://servicodados.ibge.gov.br/api/v3/agregados/8888/metadados).
O downloader verifica IDs, categoria, unidade, frequencia e dimensoes retornadas.

Formato das consultas:

```text
https://apisidra.ibge.gov.br/values/t/8880/n1/1/v/7169/p/PERIODOS/c11046/56734?formato=json
https://apisidra.ibge.gov.br/values/t/8888/n1/1/v/12606/p/PERIODOS/c544/129314?formato=json
```

`PERIODOS` e a lista explicita dos 48 meses AAAAMM, preservada em `catalog.json`.
Omitir categoria produz `..` e **nao** uma serie de volume valida.
Nao usar tabela 1737 como selecao de PMC/PIM-PF.
PMC ajustada oficial (7170) e PIM ajustada (12607) existem, mas nao sao
as variaveis selecionadas neste exercicio; o STL e calculado sobre a PMC bruta.

## Estado e revisoes

`reset` carrega as seis SGS e a PMC; PIM-PF fica **somente no cache**.
A ingestao autorizada atualiza o catalogo operacional `series`, seus metadados,
`cargas` e `vw_ultima_observacao` na mesma transacao. A consulta desse catalogo
e a evidencia de estado; esta pagina descreve a selecao, nao um espelho mutavel
da base. Cache revisado nao sobrescreve observacoes existentes silenciosamente.
Para um novo snapshot, preservar evidencias, baixar explicitamente e resetar.
