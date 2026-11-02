# Ajustes para o roteiro e slides originais

As referencias da conversa coordenadora **nao foram alteradas**.
Esta implementacao resolve as lacunas executaveis com as seguintes escolhas:

1. Acrescentar as selecoes SIDRA completas: PMC 8880/7169/c11046/56734;
   PIM-PF 8888/12606/c544/129314; territorio Brasil. Sem a categoria,
   a API retorna `..`; nao considerar a consulta a 1737 como validacao.
2. SGS 3698: usar titulo oficial de cambio livre, dolar venda, media do periodo;
   unidade oficial c.m.u./US$, equivalente a R$/US$ na janela pos-1994.
   Nao chamar genericamente toda a serie de PTAX sem essa ressalva.
3. Janela congelada 2022–2025 e extracao em 29/10/2026: trocar frases sobre
   "ultimo trimestre disponivel hoje" por **2025Q4 contra 2025Q3 da amostra**.
4. Trocar confirmacao apenas no chat por autorizacao externa vinculada ao
   digest, no terminal controlado pelo humano. Nao oferecer esse terminal ao
   agente. Nos ensaios automaticos ha autorizacao de teste, **nao humana**.
5. Atualizar a lista analytics para acumulado_12m, comparacao_trimestral,
   ajuste_sazonal e resultados_validados. O acumulado gera tambem tabela/PNG;
   nao ha uma ferramenta separada gerar_grafico nem gravar_sandbox.
6. Manter apenas STL ilustrativo aditivo robusto, periodo 12, 48 meses;
   nao anunciar X-13/VAR/ADF/KPSS implementados. Nao incluir VAR na nota.
7. Preferir o harness Copilot para os agentes atuais. Prompt files
   `.prompt.md` sao do harness **Local** na documentacao vigente; no
   Copilot/CLI, usar skills e o texto equivalente. Nao garantir os comandos
   `/nova-serie` e `/nota-conjuntura` em todos os harnesses.
8. `.vscode/mcp.json` continua disponivel para Local; o formato portavel
   `.mcp.json` atende Copilot/CLI. Nao confundir `servers` e `mcpServers`.
   IDs declarativos dos agentes: `servidor/ferramenta` ou `servidor/*`;
   o nome runtime observado na CLI e `servidor-ferramenta`.
9. A nota e renderizada de template deterministico, com numeros verificados.
   A interpretacao assistida esta no transcript do agente, sujeita a revisao.
   Nao apresentar isso como redacao livre automaticamente homologada.
10. A execucao comprovada nesta entrega foi pela **CLI GitHub Copilot real**
    com quatro agentes e tres skills, alem do cliente MCP Python.
    A UI do VS Code, descoberta dos prompt files, completions, Ask,
    confirmacao humana e ensaio cronometrado ainda exigem passagem humana.

Referencias oficiais consultadas:
[agentes](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference),
[MCP](https://code.visualstudio.com/docs/agent-customization/mcp-servers),
[prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files).
Cliente registrado nos ensaios `copilot-e2e` e `copilot-final`: **GitHub
Copilot CLI 1.0.105**, conforme seus arquivos `evidence.json`, preservados.
A sondagem inicial retornou **1.0.102**; ela nao deve ser usada como versao
do ensaio final. O momento e o mecanismo da mudanca de versao observada nao
foram verificados; esta tarefa nao executou comando de atualizacao.
