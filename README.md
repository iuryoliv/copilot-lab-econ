# Copilot Lab — Sessao 02

Laboratorio executavel local: **dados publicos reais → SQLite → quatro MCP
stdio → calculos/PNG → nota Markdown/DOCX**. Sem recursos cloud,
credenciais de producao ou recomendacao de investimento.

Este repositorio privado preserva o codigo e os assets gerados: dados publicos,
bancos SQLite, graficos, documentos, logs e evidencias dos ensaios. O ambiente
virtual e caches de execucao nao sao versionados; reconstrua-os pelo setup.
Os registros historicos foram preservados e podem conter caminhos locais do
ambiente original. Os relatos de validacao referem-se a execucao de 29/10/2026,
anterior a publicacao privada solicitada em 02/11/2026.

**Janela congelada: janeiro/2022 a dezembro/2025**, extraida em 29/10/2026.
E um exercicio historico, nao uma nota sobre a conjuntura corrente de 2026.
O ambiente foi executado pelo **GitHub Copilot CLI autenticado**, com os quatro
agentes e tres skills; isso nao comprova a UI do VS Code, completions ou Ask.
Evidencias e limites em [docs/validacao.md](docs/validacao.md).

## Preparar e reproduzir

**Windows:** siga o [guia de preparacao e execucao com WSL2](docs/windows.md).
Ele mantem Bash e `.venv/bin/python` no Linux; nao pressupoe suporte Windows
nativo nem ensaio realizado em Windows/WSL.

macOS/Linux, Python 3.13 para reproduzir o lock do ensaio; versao ensaiada: 3.13.9.
Executar na raiz deste projeto:

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q --junitxml=outputs/evidence/pytest.xml
.venv/bin/python scripts/demo_mcp.py --run ensaio-mcp-01
.venv/bin/python scripts/demo_copilot.py --run ensaio-copilot-01
```

`setup.sh` instala somente na `.venv`, a partir de `pyproject.toml` e
`requirements.lock.txt`, usa cache existente e reconstroi **somente**
`data/econ_lab.db` e `data/econ_lab_backup.db`. Cache, outputs e logs sao
preservados. Pare servidores MCP antes de resetar. Nao use nomes de ensaio ja
existentes: os scripts rejeitam sobrescrita de evidencias.

O cliente MCP Python e a CLI Copilot sao validacoes **distintas**.
`demo_copilot.py` exige `copilot` instalado e previamente autenticado. Nao faz
login, nao altera politicas, nao usa `--trust-folder`, `--allow-all` ou
`--allow-all-tools`. Se o cliente pedir confianca/autenticacao ou uma permissao
indisponivel, o operador deve resolver pessoalmente, apos revisar o pedido.
Nenhum prompt de confianca e contornado pelo script.

Os dois ensaios usam copias isoladas em `outputs/evidence/<nome>/`.
A autorizacao nesses ensaios e **automatizada, rotulada NOT-human**, nunca uma
confirmacao humana. A base principal continua com sete series e PIM-PF apenas
no cache. O ensaio Copilot usa processos reais do cliente, sem subagentes,
handoffs por memoria presumida ou simulacao de respostas.

## Demonstrar pelo Copilot no VS Code

1. Abra esta pasta no VS Code; revise `.vscode/mcp.json` e os comandos locais.
   Aprove pessoalmente qualquer pedido de confianca apropriado. Sao quatro
   servidores: `sqlite-econ`, `series-publicas`, `analytics`, `relatorios`.
   O formato portavel `.mcp.json` tambem atende ao harness Copilot/CLI;
   nao importe as duas configuracoes manualmente como servidores duplicados.
2. Confira as sete series por `listar_series` e PIM-PF por `status_cache`.
   Selecione **engenheiro-dados** e execute `/nova-serie` no harness
   **Local**. No harness **Copilot**, prompt files nao sao comandos
   garantidos: cole o texto equivalente do arquivo.
3. Revise quantidade, unidade, ajuste, extracao, URL, periodo e digest.
   No terminal externo controlado **pelo humano**, execute:

```bash
.venv/bin/python -m econlab.cli proposal IBGE_PIMPF
.venv/bin/python -m econlab.cli authorize IBGE_PIMPF DIGEST_EXATO --actor operador
```

Digite a frase solicitada pessoalmente. Autorizacao valida por dez minutos,
uma vez, vinculada ao arquivo do banco, revisao da base e cache/metadados.
Informe ao agente que a autorizacao externa foi registrada. Ele chama
`ingerir_serie_cache` e confere catalogo, view e carga. Um "sim" no chat,
sozinho, **nao** autoriza a escrita no servidor.

4. Selecione **analista-macro** e envie:

```text
Use as skills graficos-padrao e dessazonalizacao.
Calcule 36 pontos mensais de IPCA e IGP-M compostos em 12 meses.
Gere CSV e PNG. Compare PMC por STL explicito com IBC-Br ajustado pelo BCB:
ultimo trimestre completo comum versus anterior, seis meses completos.
Informe fontes, extracao e limitacoes. Valide ambos os manifestos.
```

5. Se desejar, **econometrista** pode conferir os metadados e explicar STL.
   Nao ha X-13, VAR, ADF/KPSS nem diagnósticos VAR implementados. Nao simular.
6. Passe explicitamente ao **redator-relatorios**:
   `outputs/inflacao/manifest.json`, `tabela.csv`, `grafico.png` e
   `outputs/atividade/manifest.json`, `trimestres.csv`, `pmc_stl.csv`.
   Use `/nota-conjuntura` no Local ou cole seu texto no harness Copilot.
   A ferramenta verifica hashes, numeros e versao das fontes, exporta
   `outputs/nota_conjuntura.md` e `.docx`, e reabre o DOCX por codigo.
   A nota e um template deterministico; a sintese do agente fica no transcript.

O arquivo de agente limita as ferramentas, mas nao e isolamento de sistema
operacional. Nos ensaios CLI, terminal/escrita generica sao negados e o tool
SQL interno de sessao e explicitamente excluido (`--excluded-tools=sql`).
Skills continuam disponiveis. Nao disponibilize ferramentas extras para "ajudar"
um agente a contornar esses limites.

## Dados, controles e contingencia

- [Catalogo e selecoes oficiais](docs/catalogo-de-series.md).
- [Contratos e limites de seguranca](docs/contratos.md).
- [Resultados e evidencias executadas](docs/validacao.md).
- [Ajustes necessarios no roteiro original](docs/roteiro-ajustes.md).

Para atualizar **explicitamente** o cache publico:
`.venv/bin/python -m econlab.cli download`. Ha timeout e duas repeticoes
limitadas; indisponibilidade gera erro, nunca dados inventados nem fallback
silencioso. A janela continua congelada em 2022–2025. Revisoes podem mudar
valores e hashes. Preserve antes as evidencias de um ensaio que queira guardar.

Para contingencia offline, use o cache ja validado: `reset`, MCP e analises
nao acessam a rede. O **cliente Copilot**, diferentemente dos MCP, requer acesso
ao servico e contexto pode ser processado remotamente conforme contrato/politicas.

Versao de 60 minutos: preservar ingestao autorizada, inflacao/PNG, nota e
controles; atividade ja preparada pode ser mostrada com as limitacoes.
A extensao de ajuste sazonal e executavel, mas VAR e GitHub/PR estao fora
desta implementacao. Nao houve ensaio humano cronometrado de 60/90 minutos.
