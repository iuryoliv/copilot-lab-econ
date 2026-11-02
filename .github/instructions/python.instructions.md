---
applyTo: "**/*.py"
---

Reutilize econlab.core para leitura, validacao mensal, auditoria e transacoes.
SQLite de consulta deve usar mode=ro, query_only, authorizer e quotas; regex nao
e autorizacao. Nao criar base automaticamente em consultas.
Datas ISO mensais no primeiro dia; ordenar e verificar calendario, nulos,
duplicidades e valores finitos antes de calcular. Nao preencher lacunas.
Acumulados sao produtos de fatores, nao somas. Trimestres devem ter seis meses
comuns e completos, com razao das medias. Testes sinteticos claramente rotulados.
Instale dependencias somente na .venv; execute pytest e cliente MCP stdio.
Logs de erros explicitos, sem dados pessoais, credenciais ou sucesso falso.
