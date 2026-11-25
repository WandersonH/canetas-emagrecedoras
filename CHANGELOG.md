# CHANGELOG

Cada entrada diz o que mudou, por quê, o que foi executado de verdade, o que ficou pendente e onde está a evidência. As mais recentes ficam em cima.

## 25/11/2026 · Análises de texto e redes (run 45575831115)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) data/emojis.json, data/venda (triagem de venda irregular, só contagens), data/comentarios (cadernos por rede, corpus anonimizado) e data/jama (agregados da codificação manual JAMA).

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45575831115: gravado data/corpus: 37572 textos, 51679 segmentos, 11999 na CHD, 90.1% classificados, 10 classes, 3000 formas. 11 redes, 115 comunidades ≥1%, 215 centralidades, 0 erros. gravado data/manifestos/venda_irregular_20261125T083018Z.json: venda irregular, 574 candidatos em 39185 textos. comentarios youtube: 21326 comentários, 18735 autores, tom 21326, CHD sim comentarios tiktok: 443 comentários, 441 autores, tom 443, CHD não comentarios instagram: 284 comentários, 277 autores, tom 284, CHD não comentarios x: 990 comentários, 785 autores, tom 990, CHD sim . jama: 115 vídeos (117 linhas), média 1.52, na coleta 2

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45575831115 e data/corpus/chd.json.

## 25/11/2026 · YouTube histórico (run 45575501971)

**O que mudou**

- data/youtube/historico.json: estimativa e vídeos lidos por termo e mês; manifesto do run.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h28: carga histórica do YouTube, pronta para sexta-feira 27/11.

**O que foi executado de verdade**

- Workflow 'YouTube histórico', run 45575501971: gravado data/manifestos/youtube_historico_20261125T082135Z.json: 264 de 825 pares termo × mês, 106 neste run, 7871 vídeos distintos (cota esgotada)

**O que ficou pendente**

- Seguir rodando um por dia até completar todos os pares termo × mês.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45575501971 e data/youtube/historico.json.

## 24/11/2026 · Tom dos comentários com limite de tempo por execução

**O que mudou**

- `analise_comentarios.py`: o modelo de tom roda até `--tom-minutos` (padrão 25) e grava no cache o que classificou; o resto fica para a próxima execução. Comentário em inglês ou espanhol não passa mais pelo modelo, porque já fica fora da análise.

**Por quê**

- No run 45417321597 o modelo classificou 27.129 comentários de uma vez, em CPU, e o passo das análises levou cerca de 70 minutos. Sem limite, um lote grande de comentários novos estouraria o tempo do workflow e perderia o cache, que só é gravado no fim.

**O que foi executado de verdade**

- Análises, run 45417321597 (sucesso):
  - tom em 21.326 comentários do YouTube, 443 do TikTok, 284 do Instagram e 990 do X;
  - JAMA: 115 vídeos (117 linhas), média 1,52;
  - 11 redes com medidas e 0 erros.
  Página conferida no navegador com os dados gravados.
- Transcrição, run 45417327341, rede "semente": 87 de 115 vídeos transcritos e 14.208 palavras. As 28 falhas são do TikTok: IP bloqueado, post que pede login ou post indisponível. Lista no manifesto do run.
- `python -m unittest discover -s tests` antes deste commit.

**O que ficou pendente**

- Os 28 vídeos da planilha que o TikTok bloqueou para o runner.
- O que já estava pendente na entrada dos cadernos de comentários.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45417321597, https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45417327341 e `data/manifestos/transcricao_*` deste run.

## 24/11/2026 · Análises de texto e redes (run 45417321597)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) data/emojis.json, data/venda (triagem de venda irregular, só contagens), data/comentarios (cadernos por rede, corpus anonimizado) e data/jama (agregados da codificação manual JAMA).

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45417321597: gravado data/corpus: 35859 textos, 47533 segmentos, 12000 na CHD, 75.0% classificados, 9 classes, 3000 formas. 11 redes, 118 comunidades ≥1%, 215 centralidades, 0 erros. gravado data/manifestos/venda_irregular_20261124T155357Z.json: venda irregular, 458 candidatos em 36666 textos. comentarios youtube: 21326 comentários, 18735 autores, tom 21326, CHD sim comentarios tiktok: 443 comentários, 441 autores, tom 443, CHD não comentarios instagram: 284 comentários, 277 autores, tom 284, CHD não comentarios x: 990 comentários, 785 autores, tom 990, CHD sim . jama: 115 vídeos (117 linhas), média 1.52, na coleta 2

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45417321597 e data/corpus/chd.json.

## 24/11/2026 · Transcrição (run 45417327341)

**O que mudou**

- Manifestos em data/manifestos/ e contagens em data/transcricoes/resumo.json.

**Por quê**

- Transcrição pedida pelo pesquisador em 23/11/2026; feita sem custo no runner.

**O que foi executado de verdade**

- Workflow 'Transcrição (Whisper)', run 45417327341, redes: semente.
- gravado data/manifestos/transcricao_20261124T144505Z.json: semente, 87 de 115 vídeos transcritos

**O que ficou pendente**

- Rodar as análises para levar as transcrições anonimizadas ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45417327341 e os manifestos deste run.

## 24/11/2026 · Cadernos de comentários por rede, medidas do Gephi em cada rede e painel de qualidade (JAMA)

**O que mudou**

- Comentários: a página virou um caderno por rede (YouTube, TikTok, Instagram, X e Kwai), escolhido por botões. Cada caderno tem: universo e amostra, tom, nuvem de palavras, % de comentários com cada marca do dicionário aberto (`data/config/livro_comentarios.json`), aderência ao tema, série diária com os marcos, classes da CHD, rede de palavras, rede de quem marca quem, leitor do corpus anonimizado e método com downloads. As tabelas de contagem da coleta e da transcrição ficam no fim de cada caderno, separadas por rede.
- Novo `scripts/analise_comentarios.py`, que grava:
  - `data/comentarios/<rede>.json` com os agregados;
  - `data/comentarios/<rede>_corpus.json` com o texto anonimizado, autor como código A ou C e publicação como código P;
  - os GEXF `data/redes/comentarios_<rede>_{palavras,mencoes}.gexf`.
  Comentário em inglês ou espanhol fica fora pelo mesmo filtro de idioma do corpus geral. O tom usa o modelo de sentimento em português, com cache em `terceiros/comentarios/sentimento.csv` no privado.
- Redes e análise de texto: embaixo de cada rede (similitude, palavras, fontes e termos, hashtags e as redes dos comentários) entram as medidas do painel Statistics do Gephi, as comunidades Louvain e as 5 maiores centralidades por medida. `estatisticas_redes.py` passa a incluir a similitude; `resumo_redes.py` leva as centralidades e converte NaN em null.
- Novo caderno "Qualidade da informação (JAMA)". `scripts/resumo_jama.py` lê a planilha-semente no privado e grava só agregados em `data/jama/manual.json`:
  - % por critério e distribuição da pontuação;
  - resultado por tipo de perfil e por substância (agrupamento dos rótulos em `data/config/jama.json`);
  - situação e protocolo.
  A comparação com modelos de IA fica ⛔ até chegar a planilha do outro pesquisador.
- Transcrição: a rede "semente" transcreve com Whisper a fala completa dos endereços da planilha JAMA (`collect_transcricoes.py`, limite em `coleta.json`). Fica no privado e fora do corpus geral.
- Anonimização: menção com @ seguida de uma só letra também vira [perfil].
- Panorama: o período e o marco saíram do título e foram para uma nota abaixo do texto de abertura.
- Workflow Análises: instala torch CPU, transformers e openpyxl, roda `analise_comentarios.py --tom` e `resumo_jama.py`, grava `data/comentarios` e `data/jama`; limite de tempo de 120 minutos.
- Testes novos:
  - todo JSON público precisa ser válido, sem NaN;
  - corpus de comentários anonimizado, com códigos e sem campos extras;
  - redes de menção só com códigos;
  - agregado JAMA sem link nem perfil;
  - `tests/test_jama.py`.

**Por quê**

- Pedido do pesquisador em 24/11/2026, 11h12: página de comentários no formato do Atlas, separada por rede, com as contagens no fim, e as medidas de rede que faltavam na página de análise de texto.
- Pedido do pesquisador em 24/11/2026, 11h27 e 11h33: painel da metodologia JAMA. Na resposta à pergunta sobre a IA, ele decidiu ficar só com a codificação manual e os agregados mais a planilha do outro pesquisador, sem IA até ela chegar com a validação dele.
- Pedido do pesquisador em 24/11/2026, 11h37: tirar o período do título do Panorama.
- O `estatisticas.json` tinha um NaN (assortatividade indefinida) e o navegador não lia o arquivo, o que deixava as medidas sem aparecer.

**O que foi executado de verdade**

- Local, com um clone novo do repositório privado:
  - `analise_comentarios.py` deu YouTube 21.326 comentários em português (2.473 em inglês e 1.045 em espanhol fora), TikTok 443, Instagram 284 e X 990;
  - `estatisticas_redes.py` deu 11 redes e 0 erros;
  - `resumo_jama.py` deu 115 vídeos (117 linhas), média 1,52 e 2 na coleta do projeto.
- Página conferida no navegador (playwright) nos cadernos de YouTube, TikTok, Instagram e Kwai, no leitor, na página de redes e no caderno JAMA, sem erro de console.
- As saídas locais foram descartadas. O `estatisticas.json` publicado foi refeito por `resumo_redes.py` a partir dos CSVs já publicados.
- `python scripts/build_estado.py` e `python -m unittest discover -s tests`: 139 testes OK.

**O que ficou pendente**

- Disparar Análises para gravar os cadernos, o tom e as medidas com os dados do privado.
- Disparar Transcrição com a rede "semente".
- Planilha por vídeo do outro pesquisador, com o rótulo de cada modelo e a validação dele.
- As sete categorias de tipo de conteúdo na codificação manual.
- Kappa entre codificadores.
- Revisão do agrupamento dos tipos de perfil em `data/config/jama.json`.

**Onde está a evidência**

- Este commit e os runs de Análises e Transcrição disparados em seguida.

## 24/11/2026 · Análises de texto e redes (run 45410063227)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) data/emojis.json e data/venda (triagem de venda irregular, só contagens).

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45410063227: gravado data/corpus: 35859 textos, 47533 segmentos, 12000 na CHD, 75.0% classificados, 9 classes, 3000 formas. 3 redes, 23 comunidades ≥1%, 60 centralidades, 0 erros. gravado data/manifestos/venda_irregular_20261124T141140Z.json: venda irregular, 458 candidatos em 36666 textos

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45410063227 e data/corpus/chd.json.

## 24/11/2026 · Venda irregular: triagem automática e caderno com números

**O que mudou**

- scripts/venda_irregular.py e data/config/venda_irregular.json: triagem das publicações, comentários e falas transcritas das redes desde 13/05/2022.
  - Oferta: texto com sinal forte de venda (Pix, WhatsApp, chamar no privado, entrega, telefone de contato); link, preço e "a venda" sozinhos não bastam, porque aparecem em notícia e em descrição de vídeo.
  - Tipos da oferta: oferta sem receita, produto sem registro, manipulado. À parte, "menção a golpe ou falsificação", que é relato ou alerta e não oferta.
  - Sigla com homônimo (TG, T.G., T36) só conta com o tema por perto.
  - Link, telefone e preço aparecem no público só como rótulo.
- Saídas: data/venda/agregado.json (contagens por tipo, rede e mês e frequência dos sinais) e, no privado, terceiros/venda_irregular/ com texto e autor de cada candidato para a revisão de contexto. Roda no workflow Análises.
- data/config/livro_de_codigos.json: regra de aplicação do eixo venda irregular e o código "menção a golpe ou falsificação".
- index.html: caderno Venda irregular com universo examinado, candidatos, ofertas por tipo e rede, candidatos por mês com os marcos, sinais e a regra.
- scripts/build_corpus.py: textos(limpo=False) devolve o texto cru, com links e cifrões, para a triagem.
- tests/test_venda_irregular.py.

**Por quê**

- O caderno dizia "Nenhuma coleta de redes foi executada", o que já não era verdade; o pesquisador apontou a seção em 24/11/2026 11h00.

**O que foi executado de verdade**

- Teste local com clone do privado (36.666 textos, 458 candidatos) só para conferir a regra e o desenho; saídas locais descartadas. `python -m unittest discover -s tests`. Os números publicados vêm do workflow Análises.

**O que ficou pendente**

- Revisão de contexto dos candidatos (regra 11); até lá o caderno mostra "revisados: 0".

**Onde está a evidência**

- data/config/venda_irregular.json e este commit.

## 24/11/2026 · Análises de texto e redes (run 45356332517)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) e data/emojis.json.

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45356332517: gravado data/corpus: 35859 textos, 47533 segmentos, 12000 na CHD, 75.0% classificados, 9 classes, 3000 formas. 3 redes, 22 comunidades ≥1%, 60 centralidades, 0 erros

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45356332517 e data/corpus/chd.json.

## 24/11/2026 · Anonimização de perfil colado em número; códigos de autor acima de 9.999

**O que mudou**

- scripts/anonimizar.py: arroba depois de dígito ("10@fulano") passa a ser mascarada como perfil; arroba depois de letra continua como disfarce de palavra ("Mounj@ro"). Teste novo em tests/test_anonimizar.py.
- tests/test_publico.py: o código de autor aceita quatro dígitos ou mais (A10000 em diante), porque os comentários do YouTube passaram de 9.999 autores. Os códigos já dados não mudam.

**Por quê**

- O run 45354837008 (Análises) parou no teste do corpus público: um comentário trazia nota colada em arroba, que a máscara de perfil não pegava. O teste segurou a publicação; o público não mudou.
- Com os 24.854 comentários do YouTube (run 45354189151), o corpus passou a ter autor com código de cinco dígitos.

**O que foi executado de verdade**

- Corpus montado localmente com clone novo do privado: 35.859 textos, 47.533 segmentos, 12.000 na CHD, 75,0% classificados, 9 classes; `python -m unittest tests.test_publico` passou com o corpus inteiro. Saídas locais descartadas.
- Run 45354189151 (comentários do YouTube): 24.854 comentários lidos de 300 vídeos, que informam 140.455 comentários. Run 45354486107 (carga histórica do YouTube): 158 de 825 pares termo × mês feitos, cota do dia esgotada.

**O que ficou pendente**

- Nova execução de Análises.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45354837008, data/comentarios/resumo.json e data/youtube/historico.json.

## 24/11/2026 · YouTube histórico (run 45354486107)

**O que mudou**

- data/youtube/historico.json: estimativa e vídeos lidos por termo e mês; manifesto do run.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h28: carga histórica do YouTube, pronta para sexta-feira 27/11.

**O que foi executado de verdade**

- Workflow 'YouTube histórico', run 45354486107: gravado data/manifestos/youtube_historico_20261124T081536Z.json: 158 de 825 pares termo × mês, 105 neste run, 5011 vídeos distintos (cota esgotada)

**O que ficou pendente**

- Seguir rodando um por dia até completar todos os pares termo × mês.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45354486107 e data/youtube/historico.json.

## 24/11/2026 · Comentários (run 45354189151)

**O que mudou**

- Manifestos em data/manifestos/ (com o custo de cada execução paga) e contagens em data/comentarios/resumo.json.

**Por quê**

- Decisão do pesquisador em 23/11/2026: comentários no público como texto anonimizado inteiro; autorização de gasto de 23/11/2026 18h13.

**O que foi executado de verdade**

- Workflow 'Comentários (YouTube e Apify)', run 45354189151, redes: youtube.
- gravado data/manifestos/comentarios_youtube_20261124T081324Z.json: youtube, 24854 comentários de 300 publicações

**O que ficou pendente**

- Rodar as análises para levar os comentários anonimizados ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45354189151 e os manifestos deste run.

## 24/11/2026 · Análises de texto e redes (run 45334249207)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) e data/emojis.json.

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45334249207: gravado data/corpus: 14254 textos, 19353 segmentos, 11999 na CHD, 80.4% classificados, 9 classes, 3000 formas. 3 redes, 24 comunidades ≥1%, 60 centralidades, 0 erros

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45334249207 e data/corpus/chd.json.

## 24/11/2026 · Dados públicos e checagens das agências (run 45331564217)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45331564217, frentes: agencias camara.
- gravado data/manifestos/checagens_agencias_20261124T053428Z.json: 19 checagens de agências brasileiras
- gravado data/manifestos/dados_publicos_20261124T053454Z.json: camara, 60 proposições

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45331564217 e os manifestos deste run.

## 24/11/2026 · Coletas grátis (run 45331537196)

**O que mudou**

- Manifestos em data/manifestos/, resultados públicos em data/youtube, data/trends, data/imprensa e data/checagens, e data/estado.json.

**Por quê**

- Coletas grátis pedidas pelo pesquisador em 23/11/2026, no período lido de data/config/projeto.json.

**O que foi executado de verdade**

- Workflow 'Coletas grátis', disparo manual, run 45331537196, frentes: trends imprensa checagens.
- gravado data/manifestos/trends_20261124T051150Z.json: 4 de 4 grupos
- gravado data/manifestos/imprensa_20261124T051456Z.json: 7417 notícias, 29 consultas no limite
- gravado data/manifestos/checagens_20261124T053348Z.json: 8 checagens no período
- gravado data/estado.json: 9 frentes, 9 com coleta

**O que ficou pendente**

- Escolha do marco e das janelas; leitura e codificação do conteúdo coletado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45331537196 e os manifestos deste run em data/manifestos/.

## 24/11/2026 · Página no padrão do Atlas: linha do tempo, gráficos e redes vivas

**O que mudou**

- data/config/projeto.json: linha_do_tempo com 22 marcos desde 13/05/2022 (aprovação da tirzepatida pela FDA), cada um com data, lugar, tipo (aprovação, mercado, regra, fiscalização, SUS, patente), descrição e fonte. Marcos novos, conferidos na fonte em 24/11/2026: FDA aprova Mounjaro (13/05/2022); Anvisa aprova Wegovy (02/01/2023) e Mounjaro (25/09/2023); alerta de Ozempic falsificado (03/11/2023); Wegovy nas farmácias (19/07/2024); liraglutida da EMS autorizada (23/12/2024); Mounjaro nas farmácias (maio de 2025, data aproximada marcada); proibição da manipulação de semaglutida (22/08/2025); novas regras de prescrição (16/01/2026); genéricos de liraglutida (08/09/2026); Wegovy em comprimido (04/11/2026). Os demais vêm dos marcos candidatos já levantados.
- index.html:
  - linha do tempo no Panorama e no Recorte (números clicáveis que levam ao marco e à fonte);
  - gráfico mensal do que foi lido desde 13/05/2022 e do total que o YouTube informa por mês, com os marcos sobrepostos; marcos também sobre o Trends e a imprensa;
  - dados públicos em gráficos: VigiMed por ano e substância, reações, gravidade, faixa etária, sexo e UF; SNGPC por mês e substância e por UF; Câmara por mês e tipo; registro e CMED por substância e empresa. As tabelas ficam em blocos recolhíveis;
  - redes vivas (similitude, palavras, fontes e termos, hashtags): zoom pela roda do mouse, arraste, foco nos vizinhos ao passar o mouse, painel do nó (frequência, grau, força, comunidade, vizinhos mais fortes, botão que abre os segmentos), legenda que liga e desliga comunidades ou redes, busca, controle de rótulos, tabela ordenável e o .gexf para o Gephi.
- scripts/redes.py: o desenho guarda, para cada nó, as quatro ligações mais fortes (o .gexf continua com a rede inteira) e diz isso no arquivo.
- scripts/build_corpus.py:
  - rede de hashtags (hashtag usada em 5 textos ou mais, por 3 autores ou mais), em data/redes/hashtags.gexf e no desenho;
  - data/corpus/volume.json com textos por fonte e mês;
  - a rede de fontes e termos mostra todos os termos e as 14 contas ou veículos com mais textos de cada rede.

**Por quê**

- Pedido do pesquisador em 24/11/2026 02h06: "cadê a rede gephi", "dado aberto tá formatado só em tabela, gráficos", "cadê a essência do ODI Atlas", "primeira aprovação mundial nos Estados Unidos em 13 de maio de 2022 ... com marcos regulatórios Brasil linha do tempo", "redes da coleta pesquisa até o momento".

**O que foi executado de verdade**

- Corpus montado localmente com clone do privado (12.785 textos; 10 classes; 75,7% classificados) para conferir o desenho; página aberta em navegador sem cabeça, sem erro de script, com clique num nó, abertura dos segmentos e clique num marco. As saídas locais foram descartadas; o corpus publicado é o do workflow Análises. `node --check` e `python -m unittest discover -s tests`.

**O que ficou pendente**

- Rodar Análises depois das coletas gratuitas desde 2022, para a página trazer os dados novos.

**Onde está a evidência**

- data/config/projeto.json (linha_do_tempo, com a fonte de cada marco) e este commit.

## 24/11/2026 · Coletas gratuitas desde 13/05/2022; referência do critério de qualidade

**O que mudou**

- data/config/projeto.json: nova janela periodo_lido_gratuitas, de 13/05/2022 (primeira aprovação da tirzepatida no mundo, nos Estados Unidos) até a data da coleta, com a decisão registrada. A janela das redes pagas segue desde 01/01/2025.
- scripts/rede.py: periodo_lido(gratuita=True) usa a janela das gratuitas. Usam essa janela: YouTube (recente e carga histórica), Google Trends, imprensa, Fact Check Tools, checagens das agências, Câmara e Anvisa. Redes pagas, comentários e transcrição seguem desde 01/01/2025.
- A carga histórica do YouTube continua do mês mais recente para o mais antigo: termina 2025 e 2026 e depois desce até maio de 2022, conforme a cota diária.
- index.html: o panorama e o caderno Recorte mostram as duas janelas.
- data/config/livro_de_codigos.json e projeto.json: referência de aplicação dos critérios de qualidade a vídeos (Zhang et al., 2020, Annals of Translational Medicine), com a regra de 0 a 4 pontos e a medida de popularidade por visualizações por dia; o índice completo da referência pede descurtidas, que as plataformas não informam (⛔). O PDF ficou no repositório privado (semente/referencias/).

**Por quê**

- Decisão do pesquisador em 24/11/2026 02h09 (chat): "Sim, gratuitas desde 13/05/2022", e o envio do artigo como "referência do JAMA".

**O que foi executado de verdade**

- `python -m unittest discover -s tests`. Commit 756c242 no repositório privado com o PDF.

**O que ficou pendente**

- Coletar de novo Trends, imprensa, checagens, agências e Câmara com a janela nova. YouTube de 2022 a 2024: depois de sexta, pela cota.

**Onde está a evidência**

- data/config/projeto.json (janelas.periodo_lido_gratuitas) e este commit.

## 24/11/2026 · Transcrição (run 45313803598)

**O que mudou**

- Manifestos em data/manifestos/ e contagens em data/transcricoes/resumo.json.

**Por quê**

- Transcrição pedida pelo pesquisador em 23/11/2026; feita sem custo no runner.

**O que foi executado de verdade**

- Workflow 'Transcrição (Whisper)', run 45313803598, redes: tiktok kwai.
- gravado data/manifestos/transcricao_20261124T023848Z.json: tiktok, 298 de 300 vídeos transcritos
- gravado data/manifestos/transcricao_20261124T034711Z.json: kwai, 65 de 65 vídeos transcritos

**O que ficou pendente**

- Rodar as análises para levar as transcrições anonimizadas ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45313803598 e os manifestos deste run.

## 24/11/2026 · Dados públicos e checagens das agências (run 45319450848)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45319450848, frentes: agencias.
- gravado data/manifestos/checagens_agencias_20261124T032619Z.json: 12 checagens de agências brasileiras

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45319450848 e os manifestos deste run.

## 24/11/2026 · Checagens das agências: só conta o que é checagem sobre o tema

**O que mudou**

- scripts/collect_checagens_agencias.py: cada link lido é classificado. Conta como checagem o título que cita o tema (substância, marca, caneta, emagrecer, GLP-1, obesidade) e que vem de site só de checagem (Lupa, Aos Fatos, AFP Checamos, Comprova, Boatos.org, E-farsas) ou traz marca de checagem no título (falso, #FAKE, enganoso, golpe, imita, boato...). O arquivo público traz quantos links foram lidos e quantos ficaram fora, por motivo.
- index.html mostra os descartes; scripts/build_corpus.py só leva ao corpus o que conta como checagem.

**Por quê**

- No run 45306221540 a restrição por site no g1, no Estadão e no UOL trouxe notícia comum desses veículos, muitas sem relação com o tema: os 461 links não eram 461 checagens. Reclassificados os mesmos 461 links, ficam 13 checagens (7 do Fato ou Fake, 5 do Boatos.org e 1 do Estadão Verifica) e 143 links sem o tema no título.

**O que foi executado de verdade**

- Reclassificação local de data/checagens/agencias.json do run 45306221540 com a regra nova (números acima); `python -m unittest discover -s tests`.

**O que ficou pendente**

- Nova coleta das agências com a regra; revisão de contexto das checagens contadas, que é filtro automático (regra 11).

**Onde está a evidência**

- data/checagens/agencias.json do run 45306221540 e este commit.

## 24/11/2026 · Análises de texto e redes (run 45318541315)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) e data/emojis.json.

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45318541315: gravado data/corpus: 12969 textos, 17134 segmentos, 11999 na CHD, 66.9% classificados, 8 classes, 3000 formas. 2 redes, 18 comunidades ≥1%, 40 centralidades, 0 erros

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45318541315 e data/corpus/chd.json.

## 24/11/2026 · Anonimização: arrobas de palavrão disfarçado viram asteriscos

**O que mudou**

- scripts/anonimizar.py: sequência de duas ou mais arrobas dentro de uma palavra (palavrão disfarçado) vira asteriscos do mesmo tamanho. Teste novo em tests/test_anonimizar.py.

**Por quê**

- O run 45317416916 (Análises) parou no teste do corpus público: um comentário com palavrão escrito com arrobas deixava "@" seguido de letra, que o teste trata como possível perfil. O teste segurou a publicação; nada foi gravado no público.

**O que foi executado de verdade**

- Corpus montado localmente com um clone novo do privado: 12.969 textos, 17.134 segmentos, 11.999 na CHD, 66,9% classificados, 8 classes; `python -m unittest tests.test_publico` passou. As saídas locais foram descartadas; o corpus publicado é o do workflow.

**O que ficou pendente**

- Nova execução de Análises.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45317416916 e este commit.

## 24/11/2026 · Dados públicos e checagens das agências (run 45317038053)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45317038053, frentes: camara.
- gravado data/manifestos/dados_publicos_20261124T030553Z.json: camara, 54 proposições

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45317038053 e os manifestos deste run.

## 24/11/2026 · Câmara: arquivos anuais no lugar da busca da API

**O que mudou**

- scripts/collect_camara.py lê os arquivos anuais de proposições da Câmara (2025 e 2026) e filtra ementa e indexação pelos termos, em vez da busca por palavra-chave da API v2. Universo = proposições do arquivo do ano.
- index.html: o cartão da Câmara mostra os arquivos lidos e a data de apresentação.

**Por quê**

- No run 45313922869 todas as 18 consultas à API voltaram com HTTP 400 (manifesto com bloqueios); nada foi lido.

**O que foi executado de verdade**

- `node --check` e `python -m unittest discover -s tests`.

**O que ficou pendente**

- Rodar a frente "camara" de novo.

**Onde está a evidência**

- O manifesto do run 45313922869 em data/manifestos/ (campo bloqueios).

## 24/11/2026 · Dados públicos e checagens das agências (run 45313922869)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45313922869, frentes: camara.
- gravado data/manifestos/dados_publicos_20261124T025833Z.json: camara, 0 proposições

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45313922869 e os manifestos deste run.

## 23/11/2026 · Dados públicos e checagens das agências (run 45313800629)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45313800629, frentes: vigimed sngpc.
- gravado data/manifestos/dados_publicos_20261124T023812Z.json: vigimed, 4040 notificações
- gravado data/manifestos/dados_publicos_20261124T023953Z.json: sngpc industrializados, 4221125 linhas
- gravado data/manifestos/dados_publicos_20261124T025447Z.json: sngpc manipulados, 91056 linhas

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45313800629 e os manifestos deste run.

## 24/11/2026 · Proposições da Câmara dos Deputados

**O que mudou**

- scripts/collect_camara.py: busca por palavra-chave na API de dados abertos da Câmara (substâncias e termos de busca), proposições apresentadas no período lido. O universo de cada consulta é o x-total-count que a própria API informa. Saída pública em data/dados_publicos/camara.json; frente "camara" no workflow de dados públicos.
- index.html: cartão da Câmara no caderno Dados públicos. tests/test_camara.py.

**Por quê**

- A frente "camara" estava como "não verificado" em data/config/dados_publicos.json; pedido do pesquisador para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- `node --check` no script da página e `python -m unittest discover -s tests`.

**O que ficou pendente**

- Rodar a frente no workflow. Senado: ⛔, não coletado.

**Onde está a evidência**

- Este commit e o run do workflow.

## 24/11/2026 · SNGPC em arquivos mensais comprimidos; transcrição continua de onde parou

**O que mudou**

- scripts/collect_anvisa.py: as linhas do SNGPC vão para o privado em um arquivo comprimido por mês (dados_publicos/sngpc_<tipo>/<aaaamm>.csv.gz), com gzip reproduzível.
- scripts/collect_transcricoes.py: vídeo que já tem transcrição no privado não é baixado de novo; cada execução pega os próximos mais vistos. O resumo público traz o total acumulado. data/config/coleta.json: até 300 vídeos do TikTok e 82 do Kwai por execução.
- index.html: a tabela da fala dos vídeos mostra o total acumulado.

**Por quê**

- No run 45310587332 o envio ao privado foi recusado pelo GitHub: dados_publicos/sngpc_industrializados/linhas.csv tinha 594,87 MB e o limite é 100 MB. Nada desse run chegou ao privado (nem as linhas do VigiMed); o público recebeu manifestos e agregados.
- O run 45310677443 transcreveu 59 de 60 vídeos do TikTok e 20 de 20 do Kwai; sobram vídeos no período.

**O que foi executado de verdade**

- `python -m unittest discover -s tests`, com caso novo para o arquivo mensal comprimido.

**O que ficou pendente**

- Rodar de novo vigimed e sngpc; rodar a transcrição para os próximos vídeos.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45310587332 (passo "Gravar no privado") e data/transcricoes/resumo.json.

## 23/11/2026 · Dados públicos e checagens das agências (run 45310587332)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45310587332, frentes: vigimed sngpc.
- gravado data/manifestos/dados_publicos_20261124T021215Z.json: vigimed, 4040 notificações
- gravado data/manifestos/dados_publicos_20261124T021349Z.json: sngpc industrializados, 4221125 linhas
- gravado data/manifestos/dados_publicos_20261124T023103Z.json: sngpc manipulados, 91056 linhas

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45310587332 e os manifestos deste run.

## 23/11/2026 · Transcrição (run 45310677443)

**O que mudou**

- Manifestos em data/manifestos/ e contagens em data/transcricoes/resumo.json.

**Por quê**

- Transcrição pedida pelo pesquisador em 23/11/2026; feita sem custo no runner.

**O que foi executado de verdade**

- Workflow 'Transcrição (Whisper)', run 45310677443, redes: tiktok kwai.
- gravado data/manifestos/transcricao_20261124T021332Z.json: tiktok, 59 de 60 vídeos transcritos
- gravado data/manifestos/transcricao_20261124T023021Z.json: kwai, 20 de 20 vídeos transcritos

**O que ficou pendente**

- Rodar as análises para levar as transcrições anonimizadas ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45310677443 e os manifestos deste run.

## 24/11/2026 · Transcrição: ffmpeg instalado no runner

**O que mudou**

- .github/workflows/transcricao.yml instala o ffmpeg antes da transcrição.

**Por quê**

- No run 45309396335 os 80 vídeos do TikTok e do Kwai falharam com "No such file or directory: 'ffmpeg'": a imagem atual do runner não traz o ffmpeg.

**O que foi executado de verdade**

- `python -m unittest discover -s tests`. A transcrição roda de novo no workflow.

**O que ficou pendente**

- Conferir quantos vídeos foram transcritos.

**Onde está a evidência**

- data/manifestos/transcricao_20261124T020246Z.json e transcricao_20261124T020513Z.json (campo consulta.falhas).

## 24/11/2026 · Recuperação dos comentários pagos que não chegaram ao privado

**O que mudou**

- scripts/recuperar_comentarios.py e workflow manual recuperar_comentarios.yml: refazem no privado as tabelas de comentários a partir do conjunto de dados que cada execução da Apify guardou, sem rodar ator e sem custo, e conferem o SHA-256 com o do manifesto.

**Por quê**

- O run 45306225038 (Comentários) coletou TikTok (992 comentários), Instagram (298) e X (995), com o custo gravado nos manifestos, mas o envio ao privado falhou por conflito de CHANGELOG: o run começou antes da correção de scripts/gravar_no_privado.sh. O público recebeu manifestos e contagens; o texto dos comentários não ficou no privado.

**O que foi executado de verdade**

- `python -m unittest discover -s tests` antes do commit. A recuperação roda no workflow.

**O que ficou pendente**

- Conferir no log da recuperação se o SHA-256 bateu com o dos manifestos data/manifestos/comentarios_*_20261124T0*.json.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45306225038 (passo "Gravar no privado") e os manifestos citados.

## 23/11/2026 · Comentários (run 45306225038)

**O que mudou**

- Manifestos em data/manifestos/ (com o custo de cada execução paga) e contagens em data/comentarios/resumo.json.

**Por quê**

- Decisão do pesquisador em 23/11/2026: comentários no público como texto anonimizado inteiro; autorização de gasto de 23/11/2026 18h13.

**O que foi executado de verdade**

- Workflow 'Comentários (YouTube e Apify)', run 45306225038, redes: tiktok instagram x.
- gravado data/manifestos/comentarios_tiktok_20261124T015840Z.json: tiktok, 992 comentários de 40 publicações
- gravado data/manifestos/comentarios_instagram_20261124T020001Z.json: instagram, 298 comentários de 15 publicações
- gravado data/manifestos/comentarios_x_20261124T020106Z.json: x, 995 comentários de 40 publicações

**O que ficou pendente**

- Rodar as análises para levar os comentários anonimizados ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45306225038 e os manifestos deste run.

## 23/11/2026 · Transcrição (run 45309396335)

**O que mudou**

- Manifestos em data/manifestos/ e contagens em data/transcricoes/resumo.json.

**Por quê**

- Transcrição pedida pelo pesquisador em 23/11/2026; feita sem custo no runner.

**O que foi executado de verdade**

- Workflow 'Transcrição (Whisper)', run 45309396335, redes: tiktok kwai.
- gravado data/manifestos/transcricao_20261124T020246Z.json: tiktok, 0 de 60 vídeos transcritos
- gravado data/manifestos/transcricao_20261124T020513Z.json: kwai, 0 de 20 vídeos transcritos

**O que ficou pendente**

- Rodar as análises para levar as transcrições anonimizadas ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45309396335 e os manifestos deste run.

## 24/11/2026 · Correções depois da primeira execução real: Anvisa e transcrição

**O que mudou**

- scripts/collect_anvisa.py: no SNGPC a quantidade vendida estava vazia porque a coluna se chama QT_VENDIDA (manipulados: QT_UNIDADE_FARMACOTECNICA) e o coletor procurava QTD; agora acha as duas formas. No VigiMed o ano vinha quase todo "não informado" porque DATA_NOTIFICACAO está vazia na maior parte das linhas; agora vale a primeira data preenchida entre DATA_NOTIFICACAO, data de recebimento e DATA_INCLUSAO_SISTEMA, e o agregado diz qual coluna usou. Marca passa a contar pela substância que data/config/termos.json informa (Ozempic conta como semaglutida), para não contar a mesma notificação duas vezes.
- scripts/collect_transcricoes.py: o áudio passa pelo ffmpeg a 16 kHz antes do Whisper. No run 45306501163 os 80 vídeos baixados do TikTok e do Kwai falharam ao decodificar (TypeError: a versão do PyAV instalada não aceita um argumento que o faster-whisper usa). O YouTube recusou o download dos 16 vídeos tentados ("confirme que não é um robô") e 14 passaram de 10 minutos; ele sai da lista padrão do workflow.

**Por quê**

- Execução real dos runs 45306221540 e 45306501163 (manifestos em data/manifestos/).

**O que foi executado de verdade**

- `python -m unittest discover -s tests`, com casos novos para as colunas reais do SNGPC e para a data do VigiMed.

**O que ficou pendente**

- Rodar de novo a transcrição (TikTok e Kwai) e as frentes vigimed e sngpc.

**Onde está a evidência**

- data/manifestos/transcricao_20261124T013851Z.json (campo consulta.falhas), data/dados_publicos/vigimed.json e sngpc_*.json (campo colunas_usadas).

## 24/11/2026 · Gravação no privado sem perder entrada de CHANGELOG; falha do run 45306221540 no privado

**O que mudou**

- scripts/gravar_no_privado.sh e scripts/mesclar_changelog.py: todos os workflows gravam no privado por este script. Se outro workflow gravou ao mesmo tempo, o conflito no CHANGELOG.md é resolvido mantendo as duas entradas; conflito em qualquer outro arquivo para o workflow com erro.
- tests/test_mesclar_changelog.py.

**Por quê**

- O run 45306221540 (Dados públicos e checagens das agências) coletou tudo e gravou no público, mas o envio ao privado falhou por conflito de CHANGELOG com o run 45306501163 (Transcrição), que gravou no privado ao mesmo tempo. Consequência: as linhas filtradas do VigiMed e do SNGPC desse run não ficaram no privado, embora os manifestos dele as listem em arquivos_privados. Os manifestos ficam como estão (nada é apagado); a nova execução grava as linhas e manifestos novos.

**O que foi executado de verdade**

- Simulação local com dois clones e um repositório de origem: o segundo envio entrou em conflito no CHANGELOG, o script manteve as duas entradas e gravou na segunda tentativa. `python -m unittest discover -s tests`.

**O que ficou pendente**

- Rodar de novo as frentes vigimed e sngpc para gravar as linhas no privado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45306221540 (passo "Gravar no privado") e este commit.

## 23/11/2026 · Dados públicos e checagens das agências (run 45306221540)

**O que mudou**

- Manifestos em data/manifestos/, resultados em data/dados_publicos/ e data/checagens/agencias.json.

**Por quê**

- Frentes de dados públicos e checagens brasileiras pendentes; pedido do pesquisador em 23/11/2026 para prosseguir com o que faltava coletar.

**O que foi executado de verdade**

- Workflow 'Dados públicos e checagens das agências', run 45306221540, frentes: registro cmed vigimed sngpc agencias.
- gravado data/manifestos/checagens_agencias_20261124T013613Z.json: 461 checagens de agências brasileiras
- gravado data/manifestos/dados_publicos_20261124T013646Z.json: registro, 214 de 229708 linhas
- gravado data/manifestos/dados_publicos_20261124T013700Z.json: cmed, 131 de 80072 linhas
- gravado data/manifestos/dados_publicos_20261124T013719Z.json: vigimed, 4040 notificações
- gravado data/manifestos/dados_publicos_20261124T013847Z.json: sngpc industrializados, 4221125 linhas
- gravado data/manifestos/dados_publicos_20261124T015535Z.json: sngpc manipulados, 91056 linhas

**O que ficou pendente**

- Conferir as colunas usadas em cada agregado (campo colunas_usadas) com o dicionário de dados da Anvisa.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45306221540 e os manifestos deste run.

## 23/11/2026 · Transcrição (run 45306501163)

**O que mudou**

- Manifestos em data/manifestos/ e contagens em data/transcricoes/resumo.json.

**Por quê**

- Transcrição pedida pelo pesquisador em 23/11/2026; feita sem custo no runner.

**O que foi executado de verdade**

- Workflow 'Transcrição (Whisper)', run 45306501163, redes: tiktok kwai youtube.
- gravado data/manifestos/transcricao_20261124T013851Z.json: tiktok, 0 de 60 vídeos transcritos
- gravado data/manifestos/transcricao_20261124T014154Z.json: kwai, 0 de 20 vídeos transcritos
- gravado data/manifestos/transcricao_20261124T014254Z.json: youtube, 0 de 30 vídeos transcritos

**O que ficou pendente**

- Rodar as análises para levar as transcrições anonimizadas ao corpus.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45306501163 e os manifestos deste run.

## 24/11/2026 · Página: dados públicos, checagens das agências, comentários e fala dos vídeos

**O que mudou**

- index.html: caderno Dados públicos ganha um cartão por fonte da Anvisa lida (registro, CMED, VigiMed, SNGPC industrializados e manipulados), com o arquivo de origem, as linhas do arquivo (universo) e as que citam as substâncias. Contagem pequena aparece como "<5", como vem do coletor.
- Caderno Trends, imprensa e checagens: cartão das checagens das agências brasileiras, com consultas no limite e com erro.
- Caderno Comentários: tabela por rede (publicações escolhidas, comentários informados como universo, lidos, autores distintos) e tabela da fala transcrita; o botão "abrir" mostra os segmentos anonimizados do corpus.
- A nota "Nenhum número foi lido ainda" saiu do caderno Dados públicos.

**Por quê**

- Mostrar o que as coletas novas trazem, sempre com universo e amostra.

**O que foi executado de verdade**

- `node --check` no script da página; `python -m unittest discover -s tests`.

**O que ficou pendente**

- Os cartões aparecem quando os arquivos existirem; até lá ficam fora ou em ⛔.

**Onde está a evidência**

- Este commit.

## 24/11/2026 · Transcrição com Whisper no runner

**O que mudou**

- scripts/collect_transcricoes.py: baixa o áudio dos vídeos do período com mais visualizações (TikTok 60, Kwai 20, YouTube 30, até 10 minutos cada) e transcreve com faster-whisper, modelo small, em português, sem custo. Universo = vídeos da rede já coletados no período; amostra = vídeos transcritos. Vídeo que não baixa fica no manifesto com o motivo.
- Transcrições só no privado (terceiros/transcricoes/); no público, contagens em data/transcricoes/resumo.json. O texto entra anonimizado no corpus como fonte "Fala dos vídeos".
- Workflow manual transcricao.yml, sem grupo de concorrência para não segurar as outras coletas; a gravação no privado sincroniza antes de escrever o CHANGELOG.
- data/config/coleta.json: bloco "transcricao". tests/test_transcricoes.py.

**Por quê**

- Pedido do pesquisador em 23/11/2026 ("caso precise transcrever algo") e em 23/11/2026 22h26 ("prossiga"). A etapa paga de transcrição da Apify fica de reserva.

**O que foi executado de verdade**

- `python -m unittest discover -s tests` antes do commit. A transcrição roda no workflow.

**O que ficou pendente**

- Rodar o workflow; o YouTube costuma recusar download a partir do runner, o que fica registrado como falha por vídeo.

**Onde está a evidência**

- Este commit e o run do workflow.

## 24/11/2026 · Coletores de dados públicos da Anvisa, checagens das agências e comentários

**O que mudou**

- scripts/collect_anvisa.py: registro de medicamentos, preços da CMED, VigiMed (notificações, medicamentos e reações) e SNGPC (industrializados e manipulados, meses publicados desde o início do período). Cada arquivo é lido inteiro, em fluxo; ficam as linhas que citam substância ou marca de data/config/termos.json. Universo = linhas do arquivo, contadas na leitura. Linhas com dado de paciente (VigiMed, SNGPC) só no privado; no público, contagens, com "<5" para contagem pequena.
- scripts/collect_checagens_agencias.py: Google Notícias restrito ao site de cada agência brasileira (Lupa, Aos Fatos, Estadão Verifica, Fato ou Fake, AFP Checamos, Comprova, UOL Confere, Boatos.org, E-farsas), dois grupos de termos, período lido. Saída em data/checagens/agencias.json.
- scripts/collect_comentarios.py: comentários das publicações já coletadas com mais comentários informados. YouTube pela Data API; TikTok, Instagram e X pela Apify na etapa "comentarios", com a trava de gasto. Texto e autor só no privado; no público, contagens em data/comentarios/resumo.json.
- data/config/coleta.json: bloco "comentarios" com atores, preços de referência e quantas publicações entram por rede.
- scripts/build_corpus.py e index.html: comentários e checagens das agências entram no corpus, com os textos de terceiros anonimizados.
- scripts/gravar_no_main.sh: só adiciona ao commit as pastas que existem.
- Workflows manuais dados_publicos.yml e comentarios.yml. Testes novos: test_anvisa, test_checagens_agencias, test_comentarios.

**Por quê**

- Pedido do pesquisador em 23/11/2026 22h26: "monte de coisa sem coletar ainda prossiga". A Fact Check Tools API trouxe só 6 checagens, todas em inglês.

**O que foi executado de verdade**

- `python scripts/build_estado.py` e `python -m unittest discover -s tests` (119 testes, 1 pulado) antes do commit. Os coletores ainda não rodaram com dados reais: a sandbox não alcança a Anvisa; a execução vai pelos workflows.

**O que ficou pendente**

- Rodar os dois workflows e conferir as colunas usadas pelos agregados da Anvisa (campo colunas_usadas) com o dicionário de dados.
- Comentários do YouTube dependem da cota diária, que se renova às 05h (Brasília).

**Onde está a evidência**

- Este commit, os testes novos e, depois, os runs dos workflows.

## 23/11/2026 · Análises de texto e redes (run 45303707816)

**O que mudou**

- data/corpus (corpus para o IRaMuTeQ, segmentos, CHD, similitude), data/redes (GEXF, desenhos, estatísticas) e data/emojis.json.

**Por quê**

- Análises de IRaMuTeQ e Gephi com corpus interativo, pedido do pesquisador em 23/11/2026 18h23, normalizadas pelo dicionário do IRaMuTeQ.

**O que foi executado de verdade**

- Workflow 'Análises', run 45303707816: gravado data/corpus: 11045 textos, 14984 segmentos, 12000 na CHD, 69.4% classificados, 10 classes, 3000 formas. 2 redes, 19 comunidades ≥1%, 40 centralidades, 0 erros

**O que ficou pendente**

- Nomes das classes da CHD (dados pelo pesquisador) e conferência no IRaMuTeQ com o corpus exportado.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45303707816 e data/corpus/chd.json.

## 24/11/2026 · Correção do comentário em scripts/anonimizar.py

**O que mudou**

- O comentário da máscara de link citava o domínio de um agregador de links; passou a descrevê-lo sem o domínio.

**Por quê**

- O commit cfef13f foi enviado com o teste test_sem_link_de_venda_fora_dos_testes falhando por causa desse comentário. Erro meu: o commit saiu sem conferir a última rodada dos testes.

**O que foi executado de verdade**

- `python scripts/build_estado.py` e `python -m unittest discover -s tests`, todos passando antes deste commit.

**O que ficou pendente**

- Nova execução do workflow Análises.

**Onde está a evidência**

- Este commit e o anterior (cfef13f).

## 24/11/2026 · Anonimização: máscara de link para qualquer domínio

**O que mudou**

- scripts/anonimizar.py: a máscara de link passa a pegar qualquer domínio com terminação minúscula de 2 a 6 letras (por exemplo o de um agregador de links), e não só uma lista fixa de terminações. O mesmo padrão acusa link que sobrar em tem_resto_identificavel.
- tests/test_anonimizar.py: casos com agregador de links e com terminação .ee; caso de frase sem espaço depois do ponto ("acabou.Agora"), que deve ficar igual.

**Por quê**

- O run 45302552462 (Análises) parou no teste test_sem_link_de_venda_fora_dos_testes: o corpus público trazia o domínio de um agregador de links vindo de texto de terceiros. Nada foi gravado no público; o teste segurou a publicação.

**O que foi executado de verdade**

- `python -m unittest discover -s tests` local antes do commit. Depois, nova execução do workflow Análises.

**O que ficou pendente**

- Confirmar a nova execução de Análises com o corpus que inclui as coletas pagas e a carga histórica do YouTube.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45302552462 (falha no passo Gravar no público) e os testes deste commit.

## 23/11/2026 · Universo informado pelas plataformas (run 45301606392)

**O que mudou**

- data/universo/contagens.json: total de posts das hashtags no Instagram e no TikTok, de todos os tempos, e a estimativa do YouTube por termo.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h15: planilha com estimativa de custo para coletar todo o universo.

**O que foi executado de verdade**

- Workflow 'Universo informado pelas plataformas', run 45301606392.

**O que ficou pendente**

- X e Kwai não informam total (⛔).

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45301606392 e data/universo/contagens.json.

## 24/11/2026 · Carga histórica do YouTube: mês corrente refeito só no fim

**O que mudou**

- scripts/collect_youtube_historico.py: o mês em andamento só é buscado de novo quando todos os meses anteriores estiverem feitos.

**Por quê**

- O run 45301471096 mostrou o ritmo real: 53 de 345 pares termo × mês feitos, cota diária de cerca de 100 buscas. Refazer o mês corrente todo dia gastaria 15 buscas por dia e empurraria o fim da carga para depois de sexta 27/11.

**O que foi executado de verdade**

- Run 45301471096: 53 pares recuperados do bruto, 4 buscas novas, cota esgotada, 1.744 vídeos distintos. python3 -m unittest discover -s tests: todos passaram, 1 pulado.

**O que ficou pendente**

- Faltam 292 pares: cerca de 3 runs, um por dia, de terça 24 a quinta 26/11; sexta fica de folga.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45301471096 e data/youtube/historico.json.

## 23/11/2026 · YouTube histórico (run 45301471096)

**O que mudou**

- data/youtube/historico.json: estimativa e vídeos lidos por termo e mês; manifesto do run.

**Por quê**

- Pedido do pesquisador em 23/11/2026 18h28: carga histórica do YouTube, pronta para sexta-feira 27/11.

**O que foi executado de verdade**

- Workflow 'YouTube histórico', run 45301471096: gravado data/manifestos/youtube_historico_20261124T005904Z.json: 53 de 345 pares termo × mês, 4 neste run, 1744 vídeos distintos (cota esgotada)

**O que ficou pendente**

- Seguir rodando um por dia até completar todos os pares termo × mês.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45301471096 e data/youtube/historico.json.

## 24/11/2026 · Carga histórica do YouTube: diagnóstico do run interrompido

**O que mudou**

- scripts/collect_youtube_historico.py: reconhece também os erros de limite diário (dailyLimitExceeded, rateLimitExceeded), usa tempo de espera de 20 s com 2 tentativas, mostra cada erro no log e encerra o run após 5 erros seguidos.

**Por quê**

- O run 45288852742 gravou só 53 buscas termo × mês em 90 minutos e foi cancelado. A ordem dos arquivos mostra meses pulados, sinal de erros seguidos que o coletor não reconhecia como fim de cota e que consumiam tempo em novas tentativas.

**O que foi executado de verdade**

- Run 45288852742: 53 arquivos brutos guardados no privado (bruto/youtube_historico/20261123T232749Z/), que o próximo run recupera sem nova consulta. python3 -m unittest discover -s tests: todos passaram, 1 pulado.

**O que ficou pendente**

- Próximo run com a cota renovada (por volta das 5h de Brasília) mostra no log a causa exata dos erros.

**Onde está a evidência**

- https://github.com/WandersonH/canetas-emagrecedoras/actions/runs/45288852742.

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
