# Validacao executada — 29/10/2026

**Implementacao e fluxo completos executados em cliente GitHub Copilot CLI
real autenticado**, nao apenas em funcoes Python. Projeto local dedicado:
`/Users/iurymac/Projects/copilot-lab-econ`; nenhuma publicacao, PR ou recurso
cloud foi criado. Nenhum outro projeto foi alterado.

## Evidencias principais

| Camada | Evidencia persistida | Resultado |
|---|---|---|
| Testes focados | `outputs/evidence/pytest.xml` | 44 testes; numerica, dados, controles, artefatos e MCP |
| MCP SDK real | `outputs/evidence/mcp-final/evidence.json` e `transport.json` | 20 chamadas stdio; quatro servidores |
| Copilot CLI real | `outputs/evidence/copilot-final/evidence.json` | cinco etapas, quatro agentes, tres skills, 24 chamadas MCP |
| Transcripts do cliente | `outputs/evidence/copilot-final/01-proposta.jsonl` ate `05-nota.jsonl` | tool.execution_start/complete, servidor e transporte stdio |
| Verificacao independente | `outputs/evidence/copilot-final/verification.json` | 72 celulas de inflacao, referencia oficial, trimestres e documentos |
| DOCX nativo | `outputs/evidence/copilot-final/native-word-check.json` | aberto no canvas Word; marca e quatro numeros conferidos |
| Auditoria de ingestao | `outputs/evidence/copilot-final/logs/audit.jsonl` e tabela cargas da copia | ator automatizado explicito e 48 observacoes PIM-PF |

Os registros brutos dos ensaios `copilot-e2e/evidence.json` e
`copilot-final/evidence.json` identificam **GitHub Copilot CLI 1.0.105**.
A sondagem inicial de disponibilidade retornou **1.0.102**; portanto houve
mudanca da versao observada entre a sondagem e os registros dos ensaios.
O momento e o mecanismo dessa mudanca nao foram verificados, e esta tarefa
nao executou comando de atualizacao. A versao registrada para a execucao
final e **1.0.105**, nao 1.0.102. Os registros brutos foram preservados.
As cinco etapas efetivas: proposta com engenheiro-dados; ingestao com o mesmo
papel; analise com analista-macro; conferencia com econometrista; exportacao
com redator-relatorios. Os transcripts provam chamadas das skills
graficos-padrao, dessazonalizacao e nota-conjuntura.

Nao foi usado `task`/subagente para simular execucao pelo Copilot. O script
iniciou processos reais do cliente autenticado, restringiu permissoes e
passou artefatos explicitamente entre conversas independentes.
O inventario final nao expoe bash, edicao generica, task, web_fetch nem o SQL
interno de sessao. As chamadas MCP retornaram sucesso e os arquivos/base
foram conferidos independentemente da resposta textual do agente.

## Dados e numeros conferidos

Oito caches reais, cada um com 48 observacoes mensais de 2022-01 a 2025-12.
Metadados oficiais conferidos nas paginas SGS com sessao HTTP e APIs IBGE.
Detalhes no [catalogo](catalogo-de-series.md).

| Resultado historico | Valor |
|---|---:|
| IPCA composto em 12 meses, dezembro/2025 | 4.2643849046% |
| IGP-M composto em 12 meses, dezembro/2025 | -1.0421665813% |
| PMC STL, 2025Q4 contra 2025Q3 | 0.4038582005% |
| IBC-Br ajustado BCB, 2025Q4 contra 2025Q3 | 0.4008853553% |

Tabela de inflacao: 36 pontos mensais, janeiro/2023 a dezembro/2025.
Todas as **72 celulas** de taxas foram recalculadas independentemente usando
`Decimal` e os valores brutos. IPCA tambem comparado com a serie oficial
SGS 13522: **37 pontos**, dezembro/2022 a dezembro/2025, maior desvio
**0.0051580404 ponto percentual**, tolerancia de arredondamento **0.011 pp**.
As duas taxas trimestrais foram recalculadas pela razao das somas/medias
dos seis meses completos de julho a dezembro/2025.

PNG 1500x750 aberto e inspecionado; DOCX reaberto por python-docx, ZIP valido
e aberto no canvas Word nativo. Quatro numeros e a marca de revisao conferem
entre Markdown e DOCX. A nota nao tem secao VAR.

## Arquivos reais gerados pelo Copilot

Todos abaixo estao em `outputs/evidence/copilot-final/outputs/`:

- `inflacao/tabela.csv`, `inflacao/grafico.png`, `inflacao/manifest.json`.
- `atividade/pmc_stl.csv`, `atividade/trimestres.csv`, `atividade/manifest.json`.
- `nota_conjuntura.md`, `nota_conjuntura.docx`, `relatorio_manifest.json`.

Os artefatos na raiz `outputs/` sao do smoke test de dominio durante o
desenvolvimento; a execucao comprovada pelo cliente e a subpasta **copilot-final**.
Ensaios anteriores, quando presentes, sao historico de desenvolvimento, nao
substituem as evidencias finais acima.

## Controles exercitados

Testes em bases descartaveis, nunca DROP via console irrestrito na base de demo:
DDL/DML, ATTACH, PRAGMA, multiplas instrucoes, extensao, blobs e tabela
administrativa rejeitados; readonly efetivo e preservacao da base;
limites de linhas/bytes/execucao; arquivo ausente sem criacao; ingestao
sem autorizacao/expirada/consumida/proposta divergente; vinculacao ao banco;
rollback apos falha injetada no meio da carga; integridade referencial e
serie/data unica; idempotencia e rejeicao de revisao silenciosa; checksums
do cache e evidencia; logs de leitura/ingestao; adulteracao de resultados;
calendario, ordenacao, nulos, duplicidades, fatores compostos e trimestres.

No ensaio MCP final, o teste negativo chama o **servidor**, nao depende da
recusa do agente. O bloqueio e comprovado pelo retorno de erro e pela
contagem preservada. Nao ha ferramenta de sandbox generico para testar
prefixos: a superficie de escrita foi removida em vez de protegida por regex.

Houve correcoes durante o desenvolvimento: consulta de schema precisava
permitir LIKE seguro; retorno MCP passou a declarar objeto estruturado;
leitura de CTE efemera precisou do callback especifico do authorizer.
As versoes finais foram reexecutadas apos essas correcoes.

## Limites e menor intervencao humana restante

**Nao validados:** UI do VS Code, descoberta visual de agentes/prompt files,
completions/Ask, confirmacao **humana** de ingestao e ensaio cronometrado.
A lista de extensoes consultada nao comprovou Copilot Chat no VS Code;
nenhuma extensao foi instalada nem permissao de confianca contornada.
Isso nao bloqueou a execucao comprovada pela CLI ja autenticada.

Nos ensaios, o harness registrou autorizacao **automatizada, NOT-human**,
somente em copias de ensaio. **Nao houve confirmacao humana simulada.**
O fluxo humano exige revisar proposta e digitar a frase de autorizacao no
terminal externo. A base principal permanece com sete series e PIM-PF
somente em cache; backup inicial preservado.

Para homologar a experiencia visual: abrir esta pasta no VS Code, revisar
qualquer pedido de confianca, selecionar harness/papel, conferir servidores,
executar o prompt equivalente, revisar a proposta e autorizar pessoalmente
no terminal. Verificar a UI/completions/Ask e cronometrar a apresentacao.
Prompt files sao do harness Local; no Copilot, usar skills/texto equivalente.
Nao anunciar X-13, VAR, ADF/KPSS, coding agent, PR ou revisao humana como executados.

## Reproducao

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q --junitxml=outputs/evidence/pytest.xml
.venv/bin/python scripts/demo_mcp.py --run novo-mcp
.venv/bin/python scripts/demo_copilot.py --run novo-copilot
.venv/bin/python scripts/verify_outputs.py --run novo-copilot
```

Escolher nomes novos preserva evidencias. Pip check, compileall e sintaxe
Bash tambem foram conferidos. Nao houve ensaio humano de 60/90 minutos.
