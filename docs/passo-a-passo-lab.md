# Sessão 02 — Passo a passo completo do laboratório

**Rascunho — requer revisão do economista responsável.**

Este roteiro conduz o laboratório **dados públicos → SQLite → MCP →
inflação e atividade → nota Markdown/DOCX**, com prompts para copiar,
autorização de ingestão e evidências verificáveis. A sessão pressupõe ambiente
preparado: instalar dependências não faz parte dos 90 minutos de apresentação.

**Exercício histórico:** janeiro/2022 a dezembro/2025, com extração original
em 29/10/2026 UTC. A comparação de atividade é **2025Q4 contra 2025Q3**,
nunca a conjuntura corrente de 2026. Não há recomendação de investimento.
Somente dados públicos BCB/SGS e IBGE/SIDRA são usados.

## 1. Escopo, entregas e limites

Ao final, conferir a PIM-PF carregada com autorização, tabela e PNG de inflação,
comparação de atividade por método explícito e nota revisável com rastreabilidade.
O código executa os cálculos; o agente organiza as chamadas e explica resultados;
o economista revisa números, interpretação e publicação.

| Entrega | Evidência que deve ser conferida |
|---|---|
| Ingestão de `IBGE_PIMPF` | Catálogo operacional, 48 observações, view e registro em `cargas` |
| IPCA × IGP-M | 36 pontos de 2023-01 a 2025-12, CSV, PNG e manifesto |
| PMC × IBC-Br | STL ilustrativo na PMC, ajuste oficial no IBC-Br, seis meses e manifesto |
| Nota histórica | Markdown, DOCX, manifesto do relatório e marca de revisão |
| Governança | Autorização externa, auditoria e evidências de controles em cópias |

A implementação e os ensaios históricos estão descritos em
[validação](validacao.md). Eles comprovam cliente MCP Python/stdio e Copilot CLI,
**não** descoberta visual no VS Code, completions/Ask, Windows/WSL,
confirmação humana ou duração de uma apresentação. Este guia foi adaptado por
inspeção documental; não representa novo ensaio dessas experiências.

Prevalecem os [contratos reais](contratos.md), o
[catálogo de séries](catalogo-de-series.md) e os
[ajustes do roteiro original](roteiro-ajustes.md).
Não há execução implementada de VAR, ADF/KPSS ou X-13, nem módulo GitHub do
laboratório. Não os inclua como etapas ou resultados. Não há ferramentas
`gravar_sandbox` ou `gerar_grafico`: `acumulado_12m` já gera o CSV e o PNG.

## 2. Preparar o ambiente antes da sessão

Use um checkout dedicado à demonstração. No Windows, prepare primeiro o
[ambiente Linux no WSL2](windows.md); os comandos abaixo são Bash, não
PowerShell. No macOS/Linux, providencie Git, Bash e Python com venv/pip pelos
meios aprovados. Para reproduzir o lock histórico, use Python 3.13
(ensaio original: 3.13.9). O projeto declara Python `>=3.11`, mas isso não
homologa todas as combinações do lock.

Caso ainda não tenha o repositório, com acesso autorizado:

```bash
git clone https://github.com/iuryoliv/copilot-lab-econ.git
cd copilot-lab-econ
```

Se já o tiver, entre na raiz desse checkout, sem clonar por cima dele.
Todos os caminhos deste roteiro são relativos a essa raiz.

```bash
git status --short
python3 --version
export ECONLAB_ROOT="$PWD"
```

`ECONLAB_ROOT` seleciona dados, saídas e logs. Não o deixe apontando para outro
checkout ou uma cópia de ensaio sem intenção. O cliente e o terminal do operador
devem usar **o mesmo banco**; o digest depende inclusive do caminho desse arquivo.

### Setup e reset: operação destrutiva para os bancos da demonstração

**Antes de executar:** pare os servidores MCP e preserve uma cópia independente
dos bancos e artefatos que precise guardar. Tanto o setup quanto o reset
**recriam `data/econ_lab.db` e `data/econ_lab_backup.db`**; o segundo arquivo
passa a representar o novo estado inicial, não o estado anterior à operação.
Não são comandos para uma base de trabalho real.

No checkout dedicado, quando essa recriação for desejada:

```bash
bash scripts/setup.sh
```

O script cria `.venv`, instala o lock e o projeto com dependências de teste,
confere dependências e executa o reset. Usa o cache existente; **se
`data/raw/catalog.json` estiver ausente, também tenta baixar os dados públicos**.
Não remove cache, outputs ou logs. Não use `sudo pip` nem altere o Python global.

Para apenas voltar ao estado inicial depois de instalado, com o mesmo cuidado:

```bash
.venv/bin/python -m econlab.cli reset
```

O reset valida o cache e carrega seis séries SGS e `IBGE_PMC`.
`IBGE_PIMPF` fica somente no cache. Não restaure cegamente um backup antigo:
confira origem, revisão e finalidade primeiro.

Não é necessário atualizar dados para apresentar a janela congelada.
O comando abaixo é **opcional**, apenas quando houver decisão explícita de
renovar o snapshot público, preservar evidências anteriores e revisar mudanças:

```bash
.venv/bin/python -m econlab.cli download
```

Revisões das fontes podem mudar números e hashes mesmo em 2022–2025.
Download não é ingestão nem autorização; após uma revisão, prepare novamente
o estado inicial de forma explícita. Não preencha falhas de rede com dados
inventados ou troque a seleção SIDRA por aproximação.

### Cliente Copilot

Para o ensaio Copilot, instale e autentique pessoalmente a CLI conforme o
[início rápido oficial](https://docs.github.com/en/copilot/get-started/cli-quickstart)
e as políticas da organização. Confira `copilot --version`.
O script não realiza login e não contorna confiança ou permissões.
No VS Code, disponibilize Copilot/Copilot Chat conforme a instalação e confira
o harness selecionado; não pressuponha que uma extensão ou recurso esteja ativo.

Os MCP e o SQLite executam localmente via stdio. **Isso não significa que o
Copilot inteiro execute offline/localmente**: o contexto enviado ao serviço é
processado conforme contrato e políticas. Use apenas o escopo público autorizado;
não anexe secrets, dados de clientes, informações internas ou logs brutos.

## 3. Descobrir MCP, agentes, prompt files e skills

Abra a raiz do projeto no cliente escolhido e revise:

| Arquivo/recurso | Uso |
|---|---|
| [`.vscode/mcp.json`](../.vscode/mcp.json) | Configuração VS Code, chave `servers`, transporte `stdio` |
| [`.mcp.json`](../.mcp.json) | Configuração portátil Copilot/CLI, chave `mcpServers`, tipo `local` |
| [Instruções](../.github/copilot-instructions.md) | Janela, dados públicos, autorização e rastreabilidade |
| [Agentes](../.github/agents) | Papéis e listas restritas de ferramentas |
| [Skills](../.github/skills) | Procedimentos de inflação, STL e nota |
| [Prompt files](../.github/prompts) | Textos de entrada para ingestão e nota |

Não importe manualmente as duas configurações como servidores duplicados.
A configuração portátil usa `.venv/bin/python` relativo à raiz; o VS Code
declara `${workspaceFolder}` e `ECONLAB_ROOT`. O runner de ensaio gera sua própria
configuração para a cópia isolada. Não a importe na demonstração principal.

No cliente, confira a inicialização e o inventário de ferramentas antes de
apresentar. Os nomes abaixo são os declarativos `servidor/ferramenta`;
o runtime da CLI pode mostrá-los como `servidor-ferramenta`.

| Servidor | Inventário esperado |
|---|---|
| `sqlite-econ` | `listar_series`, `obter_serie`, `descrever_esquema`, `consulta_sql` |
| `series-publicas` | `status_cache`, `ingerir_serie_cache` |
| `analytics` | `acumulado_12m`, `comparacao_trimestral`, `ajuste_sazonal`, `resultados_validados` |
| `relatorios` | `listar_templates`, `renderizar_relatorio` |

Os arquivos de agente não substituem isolamento do sistema operacional.
Não disponibilize terminal, escrita genérica, SQL interno de sessão ou outros
conectores aos papéis para contornar restrições. `engenheiro-dados` usa leitura
e ingestão; `analista-macro` usa leitura e analytics; `redator-relatorios` usa
validação dos resultados e relatórios.

**Prompt file não é skill.** No harness Local, use `/nova-serie` ou
`/nota-conjuntura` apenas se aparecerem na instalação. No harness Copilot/CLI,
não garanta esses comandos: selecione o agente e cole o texto equivalente
das seções seguintes. `/nova-serie` **já fixa `IBGE_PIMPF`** no
[arquivo](../.github/prompts/nova-serie.prompt.md); não há campo de variável
para preencher. As skills são `graficos-padrao`, `dessazonalizacao` e
`nota-conjuntura`, solicitadas explicitamente nos prompts.

Se um recurso não for descoberto, não declare a UI validada. Confira raiz,
configuração e permissões; usar o texto equivalente não concede ferramentas
que o cliente não expôs. A alternativa reproduzível pela CLI está na seção 9.

## 4. Conferir o estado inicial e apresentar a arquitetura

Com `engenheiro-dados`, copie:

```text
Faça somente a conferência inicial deste laboratório histórico.
Use sqlite-econ/listar_series e sqlite-econ/descrever_esquema.
Use series-publicas/status_cache com codigo IBGE_PIMPF.
Confira sete séries carregadas e IBGE_PIMPF ausente da base, mas no cache.
Mostre códigos, unidades, frequência, ajuste e datas de referência.
Para o cache, mostre 48 meses contínuos de 2022-01-01 a 2025-12-01,
fonte, URLs, extração UTC, hashes e a proposta com digest.
Não ingira, não autorize, não use terminal e não execute testes negativos.
Se o estado for diferente, pare e descreva a divergência.
```

Oito caches não significam oito séries carregadas. As sete iniciais são
`BCB_433`, `BCB_189`, `BCB_4189`, `BCB_3698`, `BCB_24363`, `BCB_24364`
e `IBGE_PMC`. Esperam-se 48 observações mensais por série, 336 no total.
Se PIM-PF já estiver carregada, não finja uma primeira ingestão: preserve
evidências e, antes de recomeçar, decida pelo reset controlado da seção 2.

Mostre `db/schema.sql`: `fontes`, `series`, `metadados`, `cargas`,
`observacoes` e `vw_ultima_observacao`. A tabela administrativa de autorização
não é uma interface de consulta para o agente.

Para uma explicação do esquema sem alterar código, use:

```text
Explique o esquema real retornado por sqlite-econ/descrever_esquema.
Mostre como séries, fontes, cargas e observações se relacionam,
onde está o IPCA mensal e como a view seleciona a última referência.
Não suponha tabelas nem permissões que não encontrou.
```

Se estiver usando Ask e ele não tiver MCP, forneça
[o schema real](../db/schema.sql) como contexto e identifique essa limitação.
Completions/Ask são demonstrações de cliente ainda não homologadas neste
projeto; não são necessárias para executar o fluxo numérico.

## 5. Propor e autorizar a ingestão de PIM-PF

### 5.1 Proposta pelo engenheiro-dados

Use `/nova-serie` onde disponível, ou copie o prompt completo:

```text
Cadastre IBGE_PIMPF a partir do cache local, sem baixar dados.
Use series-publicas/status_cache com codigo IBGE_PIMPF.
Confira fonte IBGE/SIDRA, tabela 8888, variável 12606, classificação 544,
categoria 129314, território Brasil, índice 2022=100, frequência mensal
e ausência de ajuste sazonal. Preserve URLs e extração UTC.
Valide datas ISO, duplicidades, nulos, valores não finitos e lacunas.
Mostre banco de destino, quantidade, início/fim, metadados, hashes
e o digest do campo proposta. A janela deve ser 2022-01 a 2025-12.
PARE antes de ingerir e aguarde autorização humana externa.
Um sim no chat não autoriza. Não execute authorize nem conceda autorização,
não solicite terminal ou escrita genérica e não altere cache/metadados.
```

Compare o retorno com o catálogo: seleção correta, 48 observações, primeiro
dia de cada mês, unidade e ajuste esperados. O digest da proposta não é apenas
o SHA256 do CSV: vincula banco de destino, revisão de cargas, cache e metadados.

### 5.2 Autorização pessoal no terminal externo

**O operador humano**, na raiz do mesmo checkout e fora das ferramentas do
agente, confere novamente a proposta:

```bash
.venv/bin/python -m econlab.cli proposal IBGE_PIMPF
```

Compare com a proposta MCP. Somente se forem a mesma carga e o mesmo digest,
substitua `DIGEST_EXATO` pelo campo `proposta` completo:

```bash
.venv/bin/python -m econlab.cli authorize IBGE_PIMPF DIGEST_EXATO --actor operador
```

`operador` é o rótulo de auditoria deste exemplo, não uma identidade humana
verificada pelo software. Não inclua dados pessoais desnecessários.
Leia o resumo e digite pessoalmente **`AUTORIZAR ` seguido do digest exato**
na pergunta interativa. Não use pipe, confirmação automática nem um terminal
exposto ao agente. O comando exige terminal interativo.

A autorização vale por dez minutos, para uso único. Mudança de caminho,
base, cache ou metadados invalida a correspondência da proposta. Se houver
divergência ou expiração, pare e refaça a conferência; não ajuste o banco
administrativo manualmente para forçar a carga.

### 5.3 Ingestão pelo engenheiro-dados

Só depois da autorização externa real, substitua `DIGEST_EXATO` e copie:

```text
A autorização humana externa foi registrada para a proposta DIGEST_EXATO
de IBGE_PIMPF neste banco. Não conceda nem renove autorização.
Chame series-publicas/ingerir_serie_cache com codigo IBGE_PIMPF e
proposta DIGEST_EXATO. O servidor deve conferir validade e correspondência.
Depois use sqlite-econ/listar_series e sqlite-econ/consulta_sql
para conferir oito séries, 48 observações PIM-PF, datas, view e carga.
Mostre o resultado efetivo da ferramenta; não trate texto de sucesso
como evidência. Em erro, pare e informe a causa, sem contornar os controles.
```

Consultas de leitura que podem ser fornecidas a `consulta_sql`, uma por chamada:

```sql
SELECT COUNT(*) AS series_carregadas FROM series;
```

```sql
SELECT COUNT(*) AS linhas, MIN(data_ref) AS inicio, MAX(data_ref) AS fim
FROM observacoes WHERE codigo_serie='IBGE_PIMPF';
```

```sql
SELECT * FROM vw_ultima_observacao WHERE codigo_serie='IBGE_PIMPF';
```

```sql
SELECT id_carga, codigo_serie, linhas, status, extraido_em, executado_em, ator
FROM cargas WHERE codigo_serie='IBGE_PIMPF' ORDER BY id_carga DESC LIMIT 1;
```

Checkpoint: oito séries, PIM-PF com 48 linhas entre `2022-01-01` e
`2025-12-01`, carga `ok` e view coerente. O catálogo operacional no banco
é atualizado; não se pede ao agente editar a página de documentação.
A auditoria de ingestão em `logs/audit.jsonl` complementa `cargas`;
log de leitura sozinho não prova escrita. Não copie logs brutos para o chat.

## 6. Analisar inflação e atividade

Troque para `analista-macro` e forneça o contexto explicitamente:

```text
Este é o laboratório histórico com janela congelada 2022-01 a 2025-12.
O engenheiro conferiu a carga de IBGE_PIMPF por catálogo, contagem,
view e cargas. Confira os dados necessários pelas ferramentas;
não presuma memória da conversa anterior. Não ingira nem use terminal.
Use explicitamente as skills graficos-padrao e dessazonalizacao.

Inflação: confira BCB_433 e BCB_189 em % a.m., sem ajuste.
Chame analytics/acumulado_12m sem parâmetros para gerar 36 pontos
mensais de acumulado composto em 12 meses, 2023-01 a 2025-12,
com histórico adicional da amostra 2022-2025. Não some taxas.
Entregue outputs/inflacao/tabela.csv, grafico.png e manifest.json.
Chame analytics/resultados_validados com tipo inflacao.

Atividade: confira IBGE_PMC sem ajuste e BCB_24364 já ajustado pelo BCB.
Chame analytics/comparacao_trimestral com metodo STL explicitamente.
Use STL aditivo robusto, período 12, sobre os 48 meses da PMC.
Não reajuste o IBC-Br. Compare 2025Q4 contra 2025Q3 pelo período comum,
com seis meses completos de julho a dezembro/2025 e
100*(média atual/média anterior-1). Compare variações, não níveis.
Entregue outputs/atividade/pmc_stl.csv, trimestres.csv e manifest.json.
Chame analytics/resultados_validados com tipo atividade.

Informe unidades, método, fontes, URLs, referências ISO, extração UTC,
hashes e caminhos para passagem ao redator. STL é ilustrativo,
não ajuste oficial IBGE nem equivalente a X-13; há limitações de ponta,
amostra curta e revisões. Não represente isso como conjuntura atual,
projeção oficial ou recomendação de investimento.
```

`acumulado_12m()` tem séries e saídas fixas; não recebe códigos ou períodos.
A fórmula é `100 × (produto(1 + taxa_mensal/100) − 1)` sobre 12 meses
consecutivos. Para 36 acumulados são necessários ao menos 47 meses válidos;
o cache oferece 48. A ferramenta seleciona os 36 pontos comuns finais.

`comparacao_trimestral(metodo="STL")` já executa o ajuste e a comparação.
`ajuste_sazonal(metodo="STL")` executa o mesmo fluxo: não é uma segunda
etapa obrigatória. Não peça X-13 como substituto silencioso.
PIM-PF demonstra ingestão; a comparação de atividade implementada usa
**PMC e IBC-Br**, não passa a incluir PIM-PF automaticamente.

Abra o PNG e confira tabela e manifestos. Recalcule pelo menos um acumulado
por implementação independente e a razão das médias dos seis meses;
o ensaio CLI com verificador da seção 9 oferece uma conferência reproduzível.
Não infira que a aparência do gráfico prova exatidão numérica.
Os caminhos de analytics são fixos: nova execução pode sobrescrever essas
saídas. Preserve um conjunto completo antes de recalcular.

### Conferência opcional pelo econometrista, sem novo modelo

O papel `econometrista` pode revisar o método já executado, não estimar
ferramentas ausentes. Passe `outputs/atividade/manifest.json`,
`outputs/atividade/trimestres.csv` e `outputs/atividade/pmc_stl.csv`:

```text
Confira IBGE_PMC e BCB_24364 com sqlite-econ/obter_serie e consulte
analytics/resultados_validados com tipo atividade. Os artefatos são
outputs/atividade/manifest.json, outputs/atividade/trimestres.csv
e outputs/atividade/pmc_stl.csv. Não presuma memória de outro agente.
Explique por que não reajustar IBC-Br, por que STL não equivale a X-13
e quais são os limites de comparar variações de índices de bases distintas.
Mantenha 2025Q4 contra 2025Q3. Não gere novos modelos ou resultados,
não use terminal e não altere os artefatos.
```

## 7. Passar os artefatos ao redator e gerar a nota

Selecione `redator-relatorios`. Os caminhos devem pertencer **ao mesmo
conjunto validado e à mesma raiz MCP**. Em uma cópia de ensaio, use os caminhos
daquela cópia; não misture manifestos históricos com tabelas recém-geradas.
O renderer não aceita caminhos livres: lê as saídas fixas da raiz configurada.

Use `/nota-conjuntura` onde descoberto, ou copie:

```text
Use a skill nota-conjuntura. Entradas explicitamente fornecidas
da raiz MCP desta demonstração:
outputs/inflacao/manifest.json
outputs/inflacao/tabela.csv
outputs/inflacao/grafico.png
outputs/atividade/manifest.json
outputs/atividade/trimestres.csv
outputs/atividade/pmc_stl.csv

Não presuma memória de outra conversa nem confie só no resumo do analista.
Chame analytics/resultados_validados com tipo inflacao e depois atividade.
Se qualquer validação falhar, pare sem renderizar.
Consulte relatorios/listar_templates e chame
relatorios/renderizar_relatorio com template nota-conjuntura.
Exporte outputs/nota_conjuntura.md e outputs/nota_conjuntura.docx,
com outputs/relatorio_manifest.json.
O tema é inflação e atividade de 2025Q4 contra 2025Q3,
na janela histórica congelada 2022-2025, não conjuntura atual de 2026.
Preserve números calculados, unidades, fontes, URLs, referências ISO,
extração UTC, hashes e limitações STL. Não invente seções ou resultados,
não faça recomendação de investimento e não use terminal/ingestão.
Inclua: Rascunho — requer revisão do economista responsável.
Informe os caminhos e o resultado efetivo da exportação.
```

A nota é **template determinístico**, não redação livre automaticamente
homologada. As validações comparam hashes, versão das fontes e consistência
numérica; o renderer reabre o DOCX por código. A síntese assistida do agente
fica na conversa/transcript e continua sujeita a revisão.

O operador abre Markdown, DOCX e PNG, compara os quatro números de destaque
(IPCA, IGP-M, PMC e IBC-Br) com os manifestos e tabelas e verifica a marca
**Rascunho — requer revisão do economista responsável**. Só então registra
a revisão humana que realmente ocorreu, sem confundi-la com autorização
de carga ou verificação automática.

## 8. Evidências, controles e fechamento

Preserve em conjunto CSVs, PNG, dois manifestos analíticos, nota nos dois
formatos e `relatorio_manifest.json`. Mantenha URLs, extração UTC, métodos,
janela e hashes; não recorte apenas números sem sua proveniência.
Hashes detectam alterações, mas não são assinatura inviolável de um processo
local que o dono dos arquivos pode modificar.

Para demonstrar controles, use as evidências de testes/ensaios **em cópias**,
não envie SQL negativo à base da apresentação. Recusa textual do modelo
não comprova bloqueio no servidor. O leitor SQLite é restrito e não há
sandbox SQL genérico; ingestão exige autorização externa e transação.
Agentes com listas de ferramentas não equivalem a sandbox do sistema.

Ao encerrar, diferencie: autorização humana de carga; verificação automática
de números/arquivos; revisão editorial/econômica humana. Preserve somente
registros necessários conforme a política aprovada, sem expor conteúdo bruto
ou dados pessoais. Não resete antes de guardar as evidências desejadas.

## 9. Ensaio CLI reproduzível em cópias isoladas

Esta alternativa é separada da demonstração humana. **Execute antes da
ingestão humana, com sete séries na base principal e PIM-PF apenas no cache**.
Os runners copiam o estado existente; não corrigem automaticamente uma base
que já tenha oito séries. `verify_outputs.py` também exige o estado principal
com sete séries.

Com setup concluído, na raiz, use nomes novos e simples (letras, números,
hífen ou sublinhado). Os exemplos não devem existir previamente:

```bash
.venv/bin/python -m pytest -q --junitxml=outputs/evidence/pytest-ensaio-02.xml
.venv/bin/python scripts/demo_mcp.py --run ensaio-mcp-02
.venv/bin/python scripts/demo_copilot.py --run ensaio-copilot-02
.venv/bin/python scripts/verify_outputs.py --run ensaio-copilot-02
```

O XML do pytest também deve ter nome novo para preservar resultados anteriores.
Esses comandos são instruções de reprodução, não uma declaração de que foram
executados ao escrever este guia.

| Comando | O que executa e onde deixa evidências |
|---|---|
| `pytest` | Testes em bases temporárias; XML no caminho escolhido |
| `demo_mcp.py` | Cliente Python MCP real/stdio, não chat Copilot; `outputs/evidence/ensaio-mcp-02/` |
| `demo_copilot.py` | Processos reais da CLI autenticada; cinco etapas, quatro agentes e três skills; `outputs/evidence/ensaio-copilot-02/` |
| `verify_outputs.py` | Conferência independente desse ensaio Copilot e gravação de `verification.json` |

**Não é autorização humana:** os runners registram autorização automatizada
`automated-rehearsal-NOT-human` somente nas cópias de ensaio. Não reproduza
esse mecanismo na base principal nem diga que o humano confirmou.
O ensaio MCP contém chamadas negativas ao servidor restrito na cópia;
não as transfira para o console SQL da demonstração.

O runner Copilot nega shell/write, exclui o SQL interno de sessão e confere o
inventário. Se houver outros servidores globais fora de escopo, revise-os;
`demo_copilot.py` aceita `--disable-server NOME` repetido para desabilitá-los
nesse ensaio. Não amplie permissões para fazer o fluxo passar.
Falha de login, confiança ou recurso do cliente exige ação pessoal apropriada,
nunca `--allow-all` ou autorização fictícia.

Na pasta do ensaio Copilot, procure `evidence.json`, os resumos das etapas,
`authorization.json` e `verification.json`; as saídas econômicas estão na
subpasta `outputs/`. O verificador confere integridade do banco da cópia,
oito séries/384 observações, 72 células de inflação, 37 referências IPCA
contra SGS 13522, meses/taxas trimestrais, hashes, PNG, documentos e chamadas
do cliente. Não use esse comando como verificador genérico da demonstração
humana: ele exige evidência de ensaio CLI e valores do snapshot original.
Uma revisão de dados pode fazer essas referências fixas falharem e exige
investigação, não supressão da checagem.

Consultar evidência histórica em [validacao.md](validacao.md) não substitui
rodar um novo ensaio. Retorno parcial, arquivo antigo ou resposta textual do
agente não comprovam que o ensaio atual terminou.

## 10. Agenda sugerida e checklist

A agenda é uma proposta, **não um ensaio humano cronometrado**:

| Minutos (90 min) | Etapa |
|---|---|
| 00–05 | Abertura, janela histórica e limites |
| 05–15 | Tour: dados, schema, MCP, papéis, prompt files e skills |
| 15–23 | Conferência inicial e explicação do esquema/fórmula |
| 23–35 | Proposta, pausa, autorização externa e ingestão |
| 35–52 | Inflação/PNG, atividade/STL e conferência numérica |
| 52–60 | Revisão metodológica opcional pelo econometrista |
| 60–72 | Passagem explícita, nota e conferência dos documentos |
| 72–80 | Controles, evidências e limites |
| 80–90 | Fechamento e perguntas |

Em 60 minutos, reserve 5 para abertura, 10 para tour/estado inicial, 12 para
ingestão autorizada, 13 para inflação e leitura da atividade previamente
gerada/validada, 12 para nota e 8 para controles/perguntas. Identifique a
atividade preparada como execução prévia; não elimine validação de manifestos
ou autorização para caber no tempo.

Antes de apresentar:

- Confira checkout, raiz MCP, snapshot, sete séries e PIM-PF no cache.
- Preserve bancos/saídas anteriores antes de qualquer reset; pare os MCP.
- Confira ferramentas por papel e prompts prontos; não dependa de UI não ensaiada.
- Tenha CLI autenticada, terminal externo sob controle humano e digest revisável.
- Use nomes novos de ensaio e separe artefatos prévios dos da apresentação.
- Feche superfícies com informação interna; prepare exemplos validados para contingência.

## 11. Troubleshooting e contingências

| Sintoma | Conduta |
|---|---|
| MCP não inicia | Confira raiz, `.venv/bin/python`, instalação, configuração do cliente e `ECONLAB_ROOT`. Reinicie pelo cliente após corrigir; não use Python global como atalho. |
| Servidores duplicados | Confira se importou os dois formatos ou configuração de ensaio. Mantenha um conjunto para a raiz correta. |
| Agente, prompt file ou skill não aparece | Confira harness/cliente e arquivos. Cole o texto equivalente e solicite a skill explicitamente; não anuncie descoberta validada nem conceda ferramentas extras. |
| CLI sem login/confiança/permissão | O operador resolve pessoalmente conforme política. O runner não contorna a solicitação nem autentica pelo usuário. |
| Estado inicial com oito séries | Já houve carga. Preserve evidências e prepare reset controlado antes de um novo ensaio, nunca durante autorização pendente. |
| Proposta divergente ou autorização expirada | Compare banco, revisão e cache, refaça `status_cache`/`proposal` e autorize pessoalmente a proposta vigente. Não reutilize digest consumido. |
| Ingestão falha | Não declare sucesso. Confira erro, catálogo, contagem e `cargas`; não force escrita SQL ou edite autorizações. |
| Checksum ou calendário inválido | Pare. Investigue snapshot e evidências; não edite CSV/metadados para mascarar erro nem preencha lacunas. |
| API indisponível | Use cache já validado com sua extração declarada. Reset, MCP e analytics não precisam de rede; Copilot pode precisar do serviço. |
| Sem Copilot/serviço | Mostre artefatos de ensaio identificado como prévio ou use o cliente MCP Python para a camada local. Não o descreva como execução Copilot. |
| Manifesto ausente, desatualizado ou divergente | Volte ao analista na mesma raiz, regenere/valide o conjunto completo após preservar o anterior; não misture arquivos nem renderize nota inválida. |
| Método indisponível solicitado | Rejeite explicitamente. Não substitua X-13 por STL sem decisão explícita e rotulagem do método realmente executado. |
| Nome de ensaio já existe | Escolha outro `--run`; não apague evidências para liberar o nome. |
| DOCX/PNG não abre ou números divergem | Interrompa a entrega e confira erros/manifestos. Não afirme aprovação nem ensaio visual apenas porque o arquivo existe. |
| Atraso na apresentação | Reduza a revisão opcional e mostre atividade previamente validada como tal; preserve autorização, rastreabilidade e revisão da nota. |

O laboratório reduz riscos com ferramentas determinísticas e validação,
mas não garante ausência de erro nem substitui revisão do economista.
