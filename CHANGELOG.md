# CHANGELOG

Cada entrada diz o que mudou, por quê, o que foi executado de verdade, o que ficou pendente e onde está a evidência. As mais recentes ficam em cima.

## 23/11/2026 · Coletas grátis (run 45264522808)

**O que mudou**

- Manifestos em data/manifestos/, resultados públicos em data/youtube, data/trends, data/imprensa e data/checagens, e data/estado.json.

**Por quê**

- Coletas grátis pedidas pelo pesquisador em 23/11/2026, no período lido de data/config/projeto.json.

**O que foi executado de verdade**

- Workflow 'Coletas grátis', disparo manual, run 45264522808, frentes: trends imprensa checagens.
- gravado data/manifestos/trends_20261123T205640Z.json: 4 de 4 grupos
- gravado data/manifestos/imprensa_20261123T205834Z.json: 3970 notícias, 5 consultas no limite
- gravado data/manifestos/checagens_20261123T210621Z.json: 6 checagens no período
- gravado data/estado.json: 9 frentes, 3 com coleta

**O que ficou pendente**

- Escolha do marco e das janelas; leitura e codificação do conteúdo coletado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45264522808 e os manifestos deste run em data/manifestos/.

## 23/11/2026 · Sondagem de fontes públicas (run 45261842688)

**O que mudou**

- data/fontes/sondagem.json: o que cada fonte de dados públicos oferece, com HTTP, tamanho e SHA-256 da página lida; cópia das páginas em data/fontes/paginas/.

**Por quê**

- Validar se as fontes de dados públicos existem e o que publicam, antes de escrever os coletores.

**O que foi executado de verdade**

- Workflow 'Sondagem de fontes públicas', disparo manual, run 45261842688, comando: python scripts/sondar_fontes.py --run-id 45261842688.
- Resultado: anvisa_dados: HTTP 200, 152 arquivos, 3 pastas
- Resultado: sngpc_industrializados: HTTP 200, 106 arquivos, 2 pastas, meses 201401 a 202611 (105)
- Resultado: sngpc_manipulados: HTTP 200, 105 arquivos, 1 pastas, meses 201401 a 202611 (105)
- Resultado: cmed_precos: sem acesso (URLError: <urlopen error [Errno 104] Connection reset by peer>)

**O que ficou pendente**

- Baixar e ler os arquivos de cada fonte com manifesto; a sondagem só lista o que existe.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45261842688 e data/fontes/sondagem.json.

## 23/11/2026 · Sondagem: leitura de índice com endereço absoluto e cópia das páginas

**O que mudou**

- scripts/sondar_fontes.py passa a reconhecer links com endereço absoluto dentro da pasta, tenta de novo em erro de rede e guarda cópia de cada página lida em data/fontes/paginas/.

**Por quê**

- O run 45261554611 leu as três páginas da Anvisa com HTTP 200 (46.454, 33.154 e 30.957 bytes) e listou 0 arquivos: o índice usa endereço absoluto, que a primeira versão descartava. A página da CMED fechou a conexão (Connection reset by peer) e não havia nova tentativa.

**O que foi executado de verdade**

- python3 -m unittest discover -s tests: 78 testes, 1 pulado, com um caso novo de índice com endereço absoluto.

**O que ficou pendente**

- Rodar a sondagem de novo e conferir a lista de arquivos de cada fonte.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45261554611 e data/fontes/sondagem.json desse run.

## 23/11/2026 · Sondagem de fontes públicas (run 45261554611)

**O que mudou**

- data/fontes/sondagem.json: o que cada fonte de dados públicos oferece, com HTTP, tamanho e SHA-256 da página lida.

**Por quê**

- Validar se as fontes de dados públicos existem e o que publicam, antes de escrever os coletores.

**O que foi executado de verdade**

- Workflow 'Sondagem de fontes públicas', disparo manual, run 45261554611, comando: python scripts/sondar_fontes.py --run-id 45261554611.
- Resultado: anvisa_dados: HTTP 200, 0 arquivos, 0 pastas
- Resultado: sngpc_industrializados: HTTP 200, 0 arquivos, 0 pastas
- Resultado: sngpc_manipulados: HTTP 200, 0 arquivos, 0 pastas
- Resultado: cmed_precos: sem acesso (URLError: <urlopen error [Errno 104] Connection reset by peer>)

**O que ficou pendente**

- Baixar e ler os arquivos de cada fonte com manifesto; a sondagem só lista o que existe.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45261554611 e data/fontes/sondagem.json.

## 23/11/2026 · Layout do Atlas, coletores grátis, sondagem de fontes e teto de teste

**O que mudou**

- index.html refeito no padrão do Atlas (assets/atlas.css, marca e ícones), pedido do pesquisador: mesmo layout, conteúdo próprio.
- Coletores grátis: scripts/collect_youtube.py, collect_trends.py, collect_imprensa.py e collect_checagens.py, com scripts/rede.py (rede e manifesto) e data/config/trends.json.
- Workflows de disparo manual: 'Coletas grátis' (gratuitas.yml), 'Sondagem de fontes públicas' (sondagem.yml) e 'Verificar segredos' (verificar.yml).
- scripts/sondar_fontes.py (o que cada fonte de dados públicos oferece) e scripts/changelog_auto.py (entrada de CHANGELOG nos commits de workflow).
- data/config/projeto.json: período lido de 01/01/2025 até a data de cada coleta. data/config/coleta.json: frente de checagens e teto de US$ 3 na etapa de teste da Apify, com a frase de autorização.

**Por quê**

- Pedido do pesquisador em 23/11/2026 17h30: usar o layout do Atlas, coletar já YouTube, Trends, checagens e imprensa, e usar US$ 3 para teste (US$ 10 anunciados). O período amplo cobre todos os marcos candidatos; o marco escolhido depois divide o período sem nova coleta.

**O que foi executado de verdade**

- python3 scripts/build_estado.py: 9 frentes, 0 com coleta.
- python3 -m unittest discover -s tests: 77 testes, 1 pulado (a trava com teto zero não se aplica mais; a trava segue testada pelos casos sintéticos).
- Página aberta em Chrome sem interface: dados carregados, frentes em ⛔.
- Nenhuma coleta e nenhum gasto neste commit.

**O que ficou pendente**

- Rodar os três workflows e registrar os runs.
- Ativar o GitHub Pages e preencher os topics (depende do dono do repositório).
- Mostrar o custo estimado por rede antes de qualquer coleta paga; o teto de US$ 3 não autoriza rede específica.

**Onde está a evidência**

- Testes em tests/test_coletores.py, tests/test_publico.py e demais arquivos de tests/.

## 23/11/2026 · Primeiro run dos testes no GitHub

**O que mudou**

- Só este registro. Nenhum arquivo de código, de configuração ou de dados mudou.

**Por quê**

A entrada anterior deixou pendente a execução do workflow `Testes` no GitHub. Ela foi feita e fica registrada com o ID do run.

**O que foi executado de verdade**

- Workflow `Testes`, disparo manual, run `45259548892`, no commit `4348505`: concluído com sucesso. Os passos "Resumo das coletas em dia" e "Testes" passaram.
- Nenhuma coleta foi executada. Nenhum gasto foi feito.

**O que ficou pendente**

- Publicar a página: ativar o GitHub Pages no repositório (ramo `main`, pasta raiz). A sessão que montou a estrutura não tem permissão para isso.
- Preencher os topics dos dois repositórios, pelo mesmo motivo.
- Não foi possível conferir daqui quais segredos estão cadastrados. A conferência acontece no primeiro workflow que usar cada um.
- Seguem valendo as pendências da entrada abaixo.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45259548892

## 23/11/2026 · Estrutura inicial, com tudo em ⛔

**O que mudou**

- `CLAUDE.md` com as doze regras do projeto, as decisões do pesquisador e as pendências que bloqueiam coleta.
- Configuração em `data/config/`: recorte (`projeto.json`), coletas e tetos (`coleta.json`), termos em quatro famílias (`termos.json`), perfis (`atores.json`), frentes de dados públicos (`dados_publicos.json`) e livro de códigos (`livro_de_codigos.json`).
- `index.html`: página com onze cadernos. Não tem número escrito à mão; lê a configuração e `data/estado.json`.
- `scripts/autorizacao.py` (trava de gasto), `scripts/anonimizar.py` (texto de terceiros antes de ir ao público), `scripts/build_estado.py` (resumo dos manifestos) e `scripts/comum.py`.
- Testes em `tests/` e workflow `Testes`, de disparo manual.

**Por quê**

Começo do projeto. A estrutura fixa as regras antes de qualquer coleta: nenhum número sem origem, nenhum gasto sem teto e autorização, nenhum dado de terceiro no público sem anonimização.

**O que foi executado de verdade**

- `python3 scripts/build_estado.py` → `gravado data/estado.json: 8 frentes, 0 com coleta`.
- `python3 -m unittest discover -s tests` → 56 testes, todos passaram.
- `python3 scripts/autorizacao.py --etapa teste --previsto 0.01` → `BLOQUEADO: teto total da Apify é zero`, código de saída 1.
- Página aberta em Chrome sem interface (versão 153), servida por `python3 -m http.server`, em tela larga e em tela de celular. Conferidos os cadernos Panorama, Recorte, Termos de busca, Comentários e Dados públicos: os arquivos de dados carregaram e todo campo sem valor apareceu como ⛔.
- Nenhuma coleta foi executada. Nenhum gasto foi feito.

**O que ficou pendente**

- Pergunta de pesquisa e hipóteses.
- Escolha do marco e das janelas de linha de base e de núcleo. Há onze marcos candidatos em `data/config/projeto.json`; três têm algo a conferir, indicado no campo `situacao`.
- Levantamento e confirmação dos perfis monitorados.
- Regras de aplicação de cada código do livro de códigos (`operacao`).
- Conferência das marcas no cadastro da Anvisa, inclusive a grafia de uma delas, que aparece de duas formas na imprensa.
- Validação de cada frente de dados públicos; cinco ainda não foram verificadas.
- Teto e frase de autorização da Apify, e os atores de coleta de cada rede paga.
- Coletores das frentes gratuitas (YouTube, Google Trends, imprensa e dados públicos).
- O workflow `Testes` ainda não rodou no GitHub.

**Onde está a evidência**

- Marcos candidatos, termos e frentes de dados públicos: cada item tem fonte e endereço no próprio arquivo de configuração.
- Regras conferidas por teste: `tests/test_config.py`, `tests/test_autorizacao.py`, `tests/test_anonimizar.py`, `tests/test_estado.py` e `tests/test_publico.py`.
