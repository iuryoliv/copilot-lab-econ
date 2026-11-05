# Executar o laboratorio no Windows com WSL2

**Rascunho — requer revisão do economista responsável.**

O caminho recomendado e **Windows + WSL2 + distribuicao Linux**, com o
repositorio, Python, Git, Copilot CLI e servidores MCP executados no Linux.
O VS Code fica instalado no Windows e abre a pasta pela extensao WSL.
Os scripts existentes usam Bash e `.venv/bin/python`: este guia **nao afirma
compatibilidade Windows nativa**, nem propoe adaptar scripts para PowerShell,
Git Bash ou `.venv/Scripts/python.exe`.

Esta documentacao foi conferida por inspecao no **macOS**, nao por execucao
em Windows/WSL. Os ensaios historicos em [validacao.md](validacao.md) nao
homologam WSL, interface do VS Code ou confirmacao humana de ingestao.
Nenhuma instalacao ou configuracao do Windows foi executada nesta tarefa.

## 1. Preparar Windows e WSL2 pessoalmente

O usuario deve providenciar Windows compativel com WSL2, virtualizacao
habilitada e permissao da organizacao para instalar os componentes. A
[documentacao Microsoft](https://learn.microsoft.com/windows/wsl/install)
descreve Windows 11 ou Windows 10 versao 2004/build 19041 ou superior para
o fluxo simplificado; isso nao dispensa verificar suporte e politicas da TI.

**PowerShell do Windows, como administrador, somente se WSL ainda nao estiver
instalado e a instalacao estiver autorizada pelo usuario/TI:**

```powershell
wsl --install -d Ubuntu
```

Reinicie se solicitado. Abra Ubuntu e crie pessoalmente o usuario e senha
Linux. Se ja houver WSL, nao reinstale a distribuicao; confira primeiro.

**PowerShell do Windows, para conferir e entrar na distribuicao:**

```powershell
wsl --list --verbose
wsl --distribution Ubuntu
```

A distribuicao usada deve indicar **VERSION 2**. Se indicar 1, pare e siga
as orientacoes oficiais/TI para conversao; nao desregistre distribuicoes,
pois isso apaga dados. Ajuste `Ubuntu` ao nome efetivamente instalado.
Os proximos blocos `bash` pertencem ao **shell Linux no WSL**, nao ao PowerShell.

Instale pessoalmente [VS Code no Windows e a extensao WSL](https://code.visualstudio.com/docs/remote/wsl).
Habilite o comando `code` no PATH durante a instalacao quando permitido.
Na janela remota, disponibilize as extensoes GitHub Copilot/Copilot Chat
conforme a versao do VS Code, autentique-se e confirme que estao habilitadas
para o workspace WSL. Revise individualmente qualquer pedido de confianca.

## 2. Preparar ferramentas dentro do Linux

Instale **Git, Python 3.13 com suporte a venv/pip e GitHub Copilot CLI no WSL**,
pelos meios aprovados para sua distribuicao/organizacao. Nao basta te-los no
Windows. A versao Python do ensaio original foi **3.13.9**;
`pyproject.toml` declara `>=3.11`, mas isso nao comprova que todo o
`requirements.lock.txt` foi ensaiado em outras versoes ou arquiteturas.

Nao se presume que `apt install python3.13` exista no repositorio padrao da
distribuicao. Consulte o fornecedor da distribuicao e as
[instrucoes oficiais do Python para Linux](https://docs.python.org/3.13/using/unix.html).
Se for necessario compilar, use as instrucoes e dependencias oficiais,
incluindo suporte a SSL/venv; a documentacao recomenda `make altinstall`
para nao substituir o Python do sistema. Nao altere `/usr/bin/python3`,
nao adicione repositorios nao aprovados e nao instale dependencias do
laboratorio com `sudo pip`.

Para a CLI, consulte o
[inicio rapido oficial do GitHub](https://docs.github.com/en/copilot/get-started/cli-quickstart).
Uma opcao documentada, **somente depois de o usuario instalar Node.js 22+
e npm no WSL por um meio aprovado**, e:

```bash
node --version
npm --version
npm install -g @github/copilot
copilot --version
```

Use um prefixo npm gravavel pelo usuario conforme sua instalacao; nao
contorne erro de permissao com elevacao indiscriminada. A instalacao
Windows via WinGet nao substitui a CLI Linux deste fluxo.

Confira no WSL:

```bash
uname -s
git --version
command -v python3
python3 --version
command -v copilot
copilot --version
```

`uname -s` deve indicar Linux; o executavel `copilot` deve pertencer a
instalacao Linux, nao ser um `.exe` ou shim da instalacao Windows sob
`/mnt/c`. Se `python3` nao for 3.13, use a alternativa explicita da secao 4.

## 3. Clonar no filesystem Linux e abrir o VS Code

O repositorio e privado: a conta precisa ter acesso. Configure pessoalmente
a autenticacao Git HTTPS pelo mecanismo aprovado; nao coloque token na URL,
em scripts, no chat ou nos arquivos MCP.

**Shell WSL:**

```bash
mkdir -p ~/projetos
cd ~/projetos
git clone https://github.com/iuryoliv/copilot-lab-econ.git
cd copilot-lab-econ
pwd
code .
```

A URL acima e a do remote `origin` do projeto. Use uma pasta nova;
nao sobrescreva um clone existente. Prefira `/home/<usuario>/projetos/`
a `/mnt/c/...`, OneDrive ou pastas compartilhadas, para manter caminhos,
permissoes e I/O do SQLite no ambiente Linux.

Confira o indicador **WSL: Ubuntu** (ou sua distribuicao) no VS Code.
O terminal integrado deve ser Linux e estar na raiz do repositorio.
Se `code .` falhar, corrija a instalacao/extensao conforme a documentacao
do VS Code; nao prossiga numa janela local Windows por engano.

**Nao reutilize uma `.venv` criada no macOS ou Windows, nem uma `.venv`
copiada de outra pasta/distribuicao.** Ambientes virtuais dependem de
executaveis, bibliotecas e caminhos locais; crie um novo no WSL.
O clone nao inclui `.venv`. Se a pasta ja contiver uma, inspecione e
preserve o necessario antes de substitui-la pessoalmente.

## 4. Preparar o laboratorio

**Antes do setup/reset:** pare os quatro servidores MCP e qualquer ensaio
em andamento. Preserve os bancos que precisar manter e copie evidencias
importantes para um destino seguro. Tanto `setup.sh` quanto `econlab.cli
reset` **recriam `data/econ_lab.db` e `data/econ_lab_backup.db`**; o backup
tambem e renovado, nao e arquivo historico imutavel. Cargas/autorizacoes
anteriores na base recriada nao sao preservadas.

Confira tambem que `ECONLAB_ROOT` nao aponta para outra execucao. Para o
fluxo deste guia, no terminal WSL dedicado:

```bash
unset ECONLAB_ROOT
```

Se `python3 --version` indicar **3.13**, execute na raiz:

```bash
bash scripts/setup.sh
.venv/bin/python --version
.venv/bin/python -m pip check
```

O script chama `python3 -m venv .venv`, instala o lock e o projeto com
extras de teste, verifica dependencias e executa reset. Ele preserva cache,
outputs e logs, mas **baixa dados se `data/raw/catalog.json` nao existir**.
No clone completo, o cache publico ja esta presente. Nao apague o catalogo
para forcar download; uma atualizacao e uma operacao explicita separada
descrita no [README](../README.md#dados-controles-e-contingencia).

Se apenas **`python3.13`** resolver o interpretador correto, nao execute
setup com um `python3` diferente. Em uma pasta sem `.venv` anterior, use
esta sequencia equivalente, em vez de `setup.sh`, mantendo o cache existente:

```bash
python3.13 --version
test -f data/raw/catalog.json
python3.13 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.lock.txt -e '.[test]'
.venv/bin/python -m pip check
.venv/bin/python -m econlab.cli reset
```

Execute cada comando somente se o anterior terminar com sucesso. Se
`test -f` falhar, pare e confira o clone/cache antes de qualquer download.
Falha de venv, wheel, compilacao ou lock nao comprova incompatibilidade
nem sucesso: preserve o erro e confira Python, arquitetura e dependencias
Linux. Nao altere pins para esconder falhas. Nao e necessario ativar a
venv: todos os comandos do laboratorio usam seu caminho explicitamente.

## 5. Testar e executar os dois ensaios

Escolha nomes **novos a cada tentativa**, inclusive apos falha parcial.
Os exemplos abaixo nao devem ser reutilizados se a pasta correspondente
ja existir. O XML tambem precisa de nome novo para nao sobrescrever
evidencias versionadas.

**Shell WSL, raiz do projeto, apos setup bem-sucedido:**

```bash
mkdir -p outputs/evidence
.venv/bin/python -m pytest -q --junitxml=outputs/evidence/pytest-wsl-01.xml
.venv/bin/python scripts/demo_mcp.py --run wsl-mcp-01
```

Os testes usam bancos temporarios. `demo_mcp.py` usa cliente Python MCP
real e quatro processos stdio, **nao Copilot**; executa controles negativos
somente em sua copia isolada. Nao copie SQL de teste negativo para a base
de demonstracao.

Antes do ensaio Copilot, autentique a **CLI dentro do WSL**, na raiz:

```bash
copilot
```

Na interface interativa da CLI, execute `/login` e siga pessoalmente os
passos oficiais. Login Git, login da extensao VS Code e login da CLI sao
contextos distintos; nao presuma compartilhamento. A conta deve ter acesso
ao Copilot e a organizacao deve permitir CLI/MCP/modelo utilizados.
Revise qualquer pedido de confianca e encerre a sessao interativa antes
de iniciar o ensaio:

```bash
.venv/bin/python scripts/demo_copilot.py --run wsl-copilot-01
.venv/bin/python scripts/verify_outputs.py --run wsl-copilot-01
```

O verificador e especifico para **ensaio Copilot**, nao para `wsl-mcp-01`.
A CLI e um servico autenticado e pode consumir a cota da conta. O script
usa cinco etapas reais, quatro agentes e tres skills; nao efetua login
nem concede confianca. Registre `copilot --version`: a CLI vigente pode
diferir da versao historica documentada, e flags/descoberta de agentes
precisam ser conferidas em caso de erro.

Ambos os ensaios registram autorizacao **automatizada `NOT-human`**, somente
na copia isolada; isso **nao representa aprovacao humana**. O fluxo espera
a base principal inicial com sete series e PIM-PF apenas no cache. Se ela
ja recebeu ingestao manual, preserve seu estado antes de decidir por reset.

## 6. MCP e demonstracao interativa no VS Code remoto

Revise `.vscode/mcp.json` na janela WSL. Seus quatro servidores
`sqlite-econ`, `series-publicas`, `analytics` e `relatorios` usam transporte
**stdio** e `${workspaceFolder}/.venv/bin/python`, com `ECONLAB_ROOT` na
pasta remota. Confira que os processos e caminhos resolvem no **Linux WSL**,
nao no host Windows. **Nao use `.venv/Scripts/python.exe` neste fluxo.**

`.mcp.json` e a configuracao para o harness/CLI, com caminho relativo
`.venv/bin/python`; execute a partir da raiz. `demo_copilot.py` gera
`mcp-client.json` dentro de cada ensaio, resolve o Python para caminho
absoluto Linux e aponta `ECONLAB_ROOT` para a copia isolada. Nao importe
ambos os arquivos manualmente como servidores duplicados.

Para a demonstracao com ingestao humana, siga o roteiro do
[README](../README.md#demonstrar-pelo-copilot-no-vs-code): consulte primeiro
`status_cache`, revise digest da proposta, quantidade, periodo, unidade,
ajuste, URLs, extracao UTC e hashes. Entao **pare o agente** ate o operador
autorizar pessoalmente num terminal interativo WSL separado, nao por uma
ferramenta de terminal oferecida ao agente:

```bash
.venv/bin/python -m econlab.cli proposal IBGE_PIMPF
.venv/bin/python -m econlab.cli authorize IBGE_PIMPF DIGEST_EXATO --actor operador
```

Substitua `DIGEST_EXATO` pelo campo `proposta` revisado e digite pessoalmente
a frase pedida. Nao automatize com pipe. A autorizacao dura dez minutos,
vale uma vez e e vinculada ao banco, revisao e cache/metadados. O MCP nao
concede autorizacao; um "sim" no chat nao substitui `econlab authorize`.
So depois o agente pode ingerir com o mesmo digest. Nao disponibilize
shell, escrita generica ou SQL interno de sessao aos papeis para contornar
restricoes; o ensaio CLI ja aplica seus limites.

## 7. Conferir resultados e preservar rastreabilidade

O ensaio MCP grava em `outputs/evidence/wsl-mcp-01/`; o Copilot grava em
`outputs/evidence/wsl-copilot-01/`. Em cada copia, confira:

| Caminho relativo ao ensaio | Conteudo a conferir |
| --- | --- |
| `evidence.json` | Executor, etapas/chamadas e aprovacao nao humana |
| `outputs/inflacao/` | `tabela.csv`, `grafico.png`, `manifest.json` |
| `outputs/atividade/` | `trimestres.csv`, `pmc_stl.csv`, `manifest.json` |
| `outputs/` | `nota_conjuntura.md`, `.docx` e `relatorio_manifest.json` |
| `logs/audit.jsonl` | Auditoria das operacoes |

No ensaio MCP, confira tambem `transport.json`; no Copilot, os transcripts
`01-proposta.jsonl` a `05-nota.jsonl`, arquivos `.stderr`, resumos por etapa,
`authorization.json` e, apos verificacao bem-sucedida, `verification.json`.
Abra CSV/PNG e documentos para revisao; mera existencia nao comprova sucesso.
O verificador confere hashes, numeros, PNG/DOCX e evidencia da CLI, mas
nao homologa interface do VS Code nem revisao humana do conteudo.

Amostra **2022-01 a 2025-12**, somente BCB/SGS e IBGE/SIDRA: exercicio
historico, nao conjuntura corrente de 2026 nem recomendacao de investimento.
Inflacao: 36 pontos compostos em 12 meses. Atividade: PMC com **STL
ilustrativo** versus IBC-Br ja ajustado pelo BCB; STL nao equivale a X-13.
Metodo indisponivel deve falhar, sem substituicao silenciosa; nao ha etapa VAR.

Preserve unidades, datas ISO, URLs, extracao UTC, metodo e hashes do catalogo
e manifestos. Os arquivos historicos podem conter caminhos macOS; nao os
reescreva para aparentar ensaio WSL. Gere novos artefatos identificados.
Ao trocar de agente, passe os caminhos completos dos dois manifestos e
CSV/PNG daquela execucao. O redator deve validar as entradas novamente e
manter nos documentos **Rascunho — requer revisão do economista responsável.**

## Rede corporativa e falhas

Git/instalacao de pacotes, componentes remotos do VS Code e Copilot exigem
rede; download explicito do cache acessa BCB/IBGE. Reset e analises MCP
com cache validado sao locais, mas isso **nao torna a CLI Copilot offline**:
contexto pode ser processado remotamente conforme contrato e politicas.

Peça a TI a configuracao aprovada de proxy, certificados e acesso aos
servicos **tambem dentro do WSL**, sem copiar credenciais para o repositorio.
Nao desabilite verificacao TLS, nao use flags de bypass, `--allow-all`,
`--allow-all-tools` ou `--trust-folder` para destravar ensaios.
Se houver bloqueio de politica, autenticacao, confianca ou rede, pare e
preserve logs/erro; nao apresente respostas parciais como execucao validada.
