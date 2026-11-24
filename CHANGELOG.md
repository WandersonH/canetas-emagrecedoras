# CHANGELOG

Cada entrada diz o que mudou, por quê, o que foi executado de verdade, o que ficou pendente e onde está a evidência. As mais recentes ficam em cima.

## 23/11/2026 · YouTube histórico (run 45288852742)

**O que mudou**

- data/youtube/historico.json: estimativa e vídeos lidos por termo e mês; manifesto do run.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h28: carga histórica do YouTube, pronta para sexta-feira 27/11.

**O que foi executado de verdade**

- Workflow 'YouTube histórico', run 45288852742: sem resultado; ver o log

**O que ficou pendente**

- Seguir rodando um por dia até completar todos os pares termo × mês.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45288852742 e data/youtube/historico.json.

## 24/11/2026 · Kwai coletado; carga histórica do YouTube retomável

**O que mudou**

- scripts/collect_youtube_historico.py: recupera o estado a partir dos arquivos brutos guardados, grava o estado a cada 10 pares termo × mês, limita a busca a 50 minutos por run e mostra o progresso; workflow com saída sem buffer.

**Por quê**

- O primeiro run da carga histórica (45288852742) passou de 50 minutos sem gravar o estado, que só era salvo no fim; se fosse interrompido, a cota gasta se perderia.

**O que foi executado de verdade**

- Run 45288801297 (Coletas pagas, Kwai): 82 publicações no período; nos outros termos a busca do Kwai não devolveu resultado. Run 45288538468 (Reconciliar Apify): TikTok 603, Instagram 512 e X 3.386 publicações recuperadas, US$ 2,15 registrados.
- python3 -m unittest discover -s tests: todos passaram, 1 pulado.

**O que ficou pendente**

- Carga histórica do YouTube: uma rodada por dia até sexta 27/11.

**Onde está a evidência**

- Manifestos em data/manifestos/ dos runs citados.

## 23/11/2026 · Coletas pagas, etapa publicacoes (run 45288801297)

**O que mudou**

- Manifestos em data/manifestos/ (com o custo de cada execução) e agregados em data/redes/publicacoes.json.

**Por quê**

- Autorização do pesquisador em 23/11/2026 18h13: US$ 10 para coletar todas as redes, gravada em data/config/coleta.json.

**O que foi executado de verdade**

- Workflow 'Coletas pagas (Apify)', run 45288801297, etapa publicacoes, redes: kwai.
- gravado data/manifestos/kwai_20261123T232632Z.json: kwai, 82 publicações no período

**O que ficou pendente**

- Revisão de homônimos e de contexto antes de contar menções; codificação do conteúdo.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45288801297 e os manifestos deste run.

## 23/11/2026 · Reconciliação com a Apify (run 45288538468)

**O que mudou**

- Manifestos das execuções pagas que ficaram sem registro, com o custo de cada uma.

**Por quê**

- Um workflow de coleta paga foi interrompido e o gasto precisa entrar na trava antes de qualquer nova execução.

**O que foi executado de verdade**

- Workflow 'Reconciliar Apify', run 45288538468, desde 2026-11-23T21:19:00Z, etapa publicacoes.
- gravado data/manifestos/tiktok_20261123T232446Z.json: tiktok, 15 execuções, 603 publicações no período
- gravado data/manifestos/instagram_20261123T232502Z.json: instagram, 15 execuções, 512 publicações no período
- gravado data/manifestos/x_20261123T232517Z.json: x, 15 execuções, 3386 publicações no período
- total reconciliado: US$ 2.1525

**O que ficou pendente**

- Completar os termos que não chegaram a rodar.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45288538468.

## 23/11/2026 · Coleta paga interrompida: reconciliação e proteção contra execução travada

**O que mudou**

- scripts/reconciliar_apify.py e workflow 'Reconciliar Apify': recuperam execuções pagas sem manifesto, com custo, bruto e tabela.
- scripts/apify.py: cada execução tem espera máxima de 15 minutos; passado isso, é abortada e o que já coletou é aproveitado. Workflow pago com tempo limite de 330 minutos, saída sem buffer e opção de rodar só alguns termos.
- Todos os workflows instalam numpy, scipy, networkx e emoji antes dos testes.

**Por quê**

- O run 45268576129 (etapa publicacoes) passou de 2 horas e foi cancelado com uma execução do X presa. TikTok e Instagram terminaram e o bruto foi para o privado, mas o commit público falhou porque os testes novos pedem numpy, e os manifestos com o custo se perderam. Sem reconciliar, a trava de gasto não enxerga esse dinheiro.

**O que foi executado de verdade**

- python3 -m unittest discover -s tests: todos passaram, 1 pulado.

**O que ficou pendente**

- Rodar 'Reconciliar Apify' desde 2026-11-23T21:19:00Z e completar X e Kwai com o que sobrar do teto da etapa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45268576129 e, no privado, bruto/tiktok e bruto/instagram desse run.

## 23/11/2026 · IRaMuTeQ, Gephi, emojis e corpus interativo; carga histórica do YouTube e universo das plataformas

**O que mudou**

- Análises de texto e redes: scripts/build_corpus.py, chd_reinert.py, similitude.py, redes.py, estatisticas_redes.py, resumo_redes.py e texto_base.py; dicionário do IRaMuTeQ em data/config/lexique_pt.txt (142.622 linhas, sem alteração, GPL v2) e Emoji Sentiment Ranking em data/config/emoji_sentiment_ranking_v1.csv. Workflow 'Análises'.
- index.html, caderno 09: corpus, classes da CHD, árvore de similitude, rede de palavras, rede de fontes e termos, medidas das redes (Louvain, E-I) e mapa de emojis. Cada classe, forma, nó, emoji e contagem abre os segmentos do corpus, com filtro por fonte e busca.
- Carga histórica do YouTube mês a mês (scripts/collect_youtube_historico.py, workflow 'YouTube histórico'), que retoma de onde parou a cada dia.
- Universo informado pelas plataformas (scripts/contagens_plataforma.py, workflow 'Universo informado pelas plataformas'): total de posts das hashtags no Instagram e no TikTok.

**Por quê**

- Pedidos do pesquisador em 23/11/2026: análises dos três painéis de referência para pesquisadores de comunicação, com corpus interativo e normalização pelo dicionário do IRaMuTeQ (18h23); carga histórica do YouTube (18h28), pronta para sexta-feira 27/11 (18h36); planilha de estimativa do universo (18h15).

**O que foi executado de verdade**

- python3 scripts/build_corpus.py com o que estava coletado: 7.008 textos lidos, 583 fora por idioma (inglês ou espanhol), 6.425 no corpus, 6.542 segmentos, 8 classes, 75,4% classificados, 2.684 formas ativas.
- python3 scripts/estatisticas_redes.py: 2 redes, 17 comunidades com 1% ou mais dos nós. python3 -m unittest discover -s tests: 100 testes, 1 pulado. Página aberta em Chrome sem interface: classes, formas, nós e emojis clicáveis.

**O que ficou pendente**

- Rodar 'Análises' depois das coletas pagas e de cada dia da carga histórica.
- Nomes das classes da CHD e conferência no IRaMuTeQ, pelo pesquisador.

**Onde está a evidência**

- data/corpus/chd.json, data/redes/estatisticas.json e tests/.

## 23/11/2026 · Coletas pagas, etapa teste (run 45268074067)

**O que mudou**

- Manifestos em data/manifestos/ (com o custo de cada execução) e agregados em data/redes/teste.json.

**Por quê**

- Autorização do pesquisador em 23/11/2026 18h13: US$ 10 para coletar todas as redes, gravada em data/config/coleta.json.

**O que foi executado de verdade**

- Workflow 'Coletas pagas (Apify)', run 45268074067, etapa teste, redes: tiktok instagram x kwai.
- gravado data/manifestos/tiktok_20261123T211710Z.json: tiktok, 30 publicações no período
- gravado data/manifestos/instagram_20261123T211724Z.json: instagram, 30 publicações no período
- gravado data/manifestos/x_20261123T211746Z.json: x, 30 publicações no período
- gravado data/manifestos/kwai_20261123T211813Z.json: kwai, 10 publicações no período

**O que ficou pendente**

- Revisão de homônimos e de contexto antes de contar menções; codificação do conteúdo.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45268074067 e os manifestos deste run.

## 23/11/2026 · Autorização de US$ 10 e coletor das redes pagas

**O que mudou**

- data/config/coleta.json: teto total de US$ 10 com a frase do pesquisador; etapas teste 1,0, publicações 5,0, comentários 2,5, transcrição 0,5 e reserva 1,0; ator, preço de referência e itens por termo de cada rede; termos do teste (Mounjaro e caneta do Paraguai).
- scripts/collect_redes.py e scripts/apify.py: busca por termo no TikTok, Instagram (hashtag), X e Kwai, com trava de gasto antes de cada rede e teto em cada execução. Workflow 'Coletas pagas (Apify)'. Testes em tests/test_redes.py.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h13: US$ 10 para coletar todas as redes, incluindo transcrição paga se for necessária. A transcrição usa Whisper no próprio GitHub Actions, sem custo; a etapa paga fica de reserva.

**O que foi executado de verdade**

- python3 -m unittest discover -s tests: 91 testes, 1 pulado. Previsão pelos preços de referência: teste US$ 0,15; publicações US$ 4,88. Nenhuma execução paga neste commit.

**O que ficou pendente**

- Rodar a etapa de teste e comparar o custo real com a previsão antes da etapa de publicações.

**Onde está a evidência**

- data/config/coleta.json e tests/test_redes.py.

## 23/11/2026 · Página mostra YouTube, Trends, imprensa e checagens

**O que mudou**

- index.html: cartão do YouTube por termo no Panorama; séries do Trends por grupo; notícias por mês com clique que abre as manchetes do mês; veículos e termos da imprensa; tabela de checagens. Tudo lido de data/youtube, data/trends, data/imprensa e data/checagens.
- tests/test_publico.py: CHANGELOG sem marca de conflito e com as cinco seções em toda entrada.

**Por quê**

- As coletas dos runs 45261726207 (YouTube) e 45264522808 (Trends, imprensa, checagens) estavam gravadas, mas a página ainda mostrava ⛔ nesses cadernos.

**O que foi executado de verdade**

- python3 -m unittest discover -s tests: 79 testes, 1 pulado. Página aberta em Chrome sem interface nos cadernos Panorama e Trends: séries, barras e listas renderizadas a partir dos arquivos.

**O que ficou pendente**

- Ativar o GitHub Pages para a página ficar no ar.
- Cobertura do YouTube no período inteiro (busca por mês) e checagens das agências brasileiras, que a API trouxe pouco.

**Onde está a evidência**

- data/youtube/agregado.json, data/trends/ultimo.json, data/imprensa/resultados.json, data/checagens/checagens.json.

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

## 23/11/2026 · YouTube refeito do bruto do run 45261726207 e gravação sem conflito

**O que mudou**

- data/youtube/agregado.json e data/manifestos/youtube_20261123T204018Z.json, refeitos do bruto guardado no privado, sem nova consulta à API.
- scripts/gravar_no_main.sh: os workflows passam a partir do main mais recente, regenerar data/estado.json e inserir a entrada de CHANGELOG antes do commit. scripts/changelog_auto.py ganha --saida e --inserir-de. scripts/collect_youtube.py ganha --do-bruto.

**Por quê**

- O run 45261726207 coletou as quatro frentes, gravou o bruto no privado e falhou ao gravar no público: o CHANGELOG mudou no main durante a coleta (commit cb155b7) e o rebase deu conflito. Refazer pela API gastaria de novo cerca de 7.500 unidades da cota diária de 10.000.

**O que foi executado de verdade**

- python3 scripts/collect_youtube.py --privado <privado> --run-id 45261726207 --do-bruto bruto/youtube/20261123T204018Z: 3.001 vídeos distintos, 1.871 canais, 15 termos, igual ao log do run.
- python3 scripts/build_estado.py: 9 frentes, 1 com coleta. python3 -m unittest discover -s tests: todos passaram, 1 pulado.

**O que ficou pendente**

- Trends, imprensa e checagens do run 45261726207 não foram gravados no público; serão coletados de novo.
- A amostra do YouTube por termo são os 250 vídeos mais recentes; nos termos grandes ela só alcança semanas antes da coleta. Cobrir o período inteiro pede busca fatiada por mês, que passa da cota de um dia.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45261726207 e, no privado, bruto/youtube/20261123T204018Z/.

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
