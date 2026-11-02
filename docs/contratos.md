# Contratos MCP e controles

Todos os servidores sao locais stdio, implementados em `econlab.server`.
A inicializacao do cliente MCP e `tools/list` foram executados de verdade;
schemas de entrada e saida foram conferidos pelo SDK. `.vscode/mcp.json` usa
`servers`; `.mcp.json` usa `mcpServers`. Sao formatos diferentes.

| Servidor | Ferramentas | Gravacao permitida |
|---|---|---|
| sqlite-econ | listar_series, obter_serie, descrever_esquema, consulta_sql | somente log |
| series-publicas | status_cache, ingerir_serie_cache | ingestao preautorizada e log |
| analytics | acumulado_12m, comparacao_trimestral, ajuste_sazonal, resultados_validados | artefatos fixos em outputs e log |
| relatorios | listar_templates, renderizar_relatorio | Markdown/DOCX fixos em outputs e log |

Parametros de leitura: `obter_serie(codigo,inicio,fim)` com ISO;
`consulta_sql(sql,limite=1000)` com 1..5000 linhas.
`status_cache(codigo='IBGE_PIMPF')` retorna metadados, resumo e proposta.
`ingerir_serie_cache(codigo,proposta)` nao aceita autorizacao em texto livre.
`comparacao_trimestral(metodo='STL')` e `ajuste_sazonal(metodo='STL')`
rejeitam X-13. `resultados_validados(tipo)` aceita inflacao ou atividade.
`renderizar_relatorio(template='nota-conjuntura')` nao aceita caminhos livres.

## Imposto pelo servidor

Leitura SQLite: arquivo deve existir, URI `mode=ro`, `query_only=ON`,
extensoes desabilitadas, authorizer com acoes/tabelas/funcoes permitidas,
limite de linhas, resposta ate 2 MB, valor/linha ate 100 KB,
tamanho SQL/expressoes e quota de instrucoes/tempo.
`execute`, nao `executescript`, impede multiplas instrucoes.
Nao e regex como autorizacao. Funcoes perigosas, ATTACH, PRAGMA, DDL/DML e
leitura da tabela administrativa de autorizacoes sao negados. A base original
e resultados ficam separados; nao ha ferramenta de escrita SQL ou sandbox
generico. Portanto o teste de prefixo de sandbox do roteiro nao se aplica.

Ingestao: codigo deve pertencer ao catalogo, checksum CSV e evidencias devem
conferir; calendario mensal continuo, datas ISO no primeiro dia, valores
numericos finitos, sem nulos/duplicidades. A proposta vincula caminho do banco,
revisao de cargas, conteudo do cache e metadados. Exige autorizacao registrada
externamente, nao expirada, nao consumida; sua revisao e conferida dentro da
transacao. A escrita e atomica com chaves estrangeiras e chave serie/data.
Mesmo cache em nova proposta nao duplica dados; cache revisado e rejeitado.
Reusar a mesma autorizacao falha explicitamente.

Auditoria JSONL em `logs/audit.jsonl`: UTC, ferramenta, outcome, codigo,
contagens, ator e erro. `cargas` e a auditoria transacional das cargas aceitas.
Uma falha nao cria carga "ok"; deixa erro no log, sem dados parciais.
Falha de log e erro explicito, nao sucesso silencioso; arquivos/log e banco
nao constituem uma transacao distribuida. Nao ha garantia de trilha inviolavel.

## Fluxo humano e limites honestos

Autorizar exige comando externo `econlab authorize`, terminal interativo e
frase com digest exato. O MCP nao expoe `approve`, `reset`, download, terminal,
escrita de arquivo generica ou manipulacao de permissoes.

O teste automatico usa `core.approve` fora do MCP **somente em copias**
descartaveis/ensaios com ator `automated-...-NOT-human`; nao comprova uma
confirmacao humana, e esta distincao fica nas evidencias.
A API de dominio e o dono do processo Python ainda podem autorizar: isto e
um laboratorio local, nao um servico de autorizacao de producao nem sandbox OS.
Uma pessoa com acesso ao arquivo pode modifica-lo fora dos MCP.

Agentes nao recebem terminal ou edicao generica. O runner CLI nega shell/write,
exclui o tool SQL de sessao e verifica o inventario efetivamente exposto.
O leitor SQL do MCP nunca concede escrita de origem, mesmo se o agente pedir.
Nao afirmar controle do servidor com base apenas na recusa de um modelo.
Os testes negativos invocam diretamente a interface restrita em copias,
incluindo DROP, PRAGMA, multiplas instrucoes e tentativa sem autorizacao.

O renderer verifica hashes de artefatos, versao das fontes e consistencia
numerica tabela/manifesto; esses hashes detectam alteracao acidental, nao sao
assinaturas criptograficas contra um atacante que possa reescrever tudo.
Template deterministico, sem liberdade para inventar valores. A aprovacao
editorial/economica continua sendo responsabilidade humana.
