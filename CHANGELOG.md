# CHANGELOG

Cada entrada diz o que mudou, por quê, o que foi executado de verdade, o que ficou pendente e onde está a evidência. As mais recentes ficam em cima.

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
