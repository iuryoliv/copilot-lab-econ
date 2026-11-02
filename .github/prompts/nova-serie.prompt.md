---
name: nova-serie
description: Valida e propoe a ingestao da PIM-PF; aguarda autorizacao externa.
agent: engenheiro-dados
tools: ['sqlite-econ/*', 'series-publicas/*']
---

Cadastre IBGE_PIMPF a partir do cache local. Confira fonte, unidade, frequencia,
ajuste sazonal e extracao. Valide datas, duplicidades, nulos e lacunas.
Mostre quantidade, inicio/fim e proposta com digest retornada por status_cache.
PARE antes da escrita. Oriente o operador a autorizar a proposta no terminal
externo conforme README. Confirmacao no chat nao basta. Apos autorizacao,
chame ingerir_serie_cache com o digest exato e confira view, contagem e cargas.
