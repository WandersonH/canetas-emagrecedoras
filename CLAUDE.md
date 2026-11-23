# Instruções para qualquer IA ou pessoa que trabalhe neste repositório

Projeto de pesquisa sobre canetas emagrecedoras (agonistas de GLP-1: Ozempic, Wegovy, Mounjaro, Saxenda e similares) nas redes, na imprensa e nas buscas no Brasil. Autoria própria: a página, os textos e os scripts descrevem o método por si e não citam outros projetos como origem. Responda sempre em português.

## Regras

1. **CHANGELOG em toda mudança, no mesmo commit.** Cada entrada diz o que mudou, por quê, o que foi executado de verdade (ID do run ou comando), o que ficou pendente e onde está a evidência.
2. **Nada é declarado pronto sem execução com dados reais.** Dado ausente é ⛔, nunca zero.
3. **Não inventar números.** Todo número vem de arquivo, manifesto ou run identificável.
4. **Rodar os testes antes de cada commit:** `python -m unittest discover -s tests`.
5. **Nunca colocar tokens ou chaves** em código, commits, mensagens ou logs. Na configuração entra só o nome do segredo.
6. **Nunca apagar dados nem reescrever histórico** sem autorização explícita do pesquisador naquele momento.
7. **Toda amostra aparece com o universo** (quanto a plataforma informa e a fonte), quanto foi lido e como a amostra foi tirada. Universo que a plataforma não informa é ⛔. Cobertura "completa" só quando a leitura para pela data inicial, e não pelo limite.
8. **Gasto só com teto maior que zero e frase de autorização** gravados em `data/config/coleta.json`. Toda coleta paga chama `scripts/autorizacao.py` antes da primeira chamada. Nenhuma consulta de saldo ou de limites da conta. O custo fica nos manifestos e nunca aparece na página.
9. **Só perfil confirmado é coletado.** Endereço provável sem fonte fica como candidato, no repositório privado, até o pesquisador confirmar.
10. **Privacidade.** No público entram só as publicações dos perfis monitorados e os agregados. Texto e autor de terceiros vão só para o privado. Tema de saúde: relato de uso, peso, doença ou efeito colateral de pessoa comum é dado sensível. Nunca aparece no público com autor, nem como trecho que permita achar a pessoa pela busca.
11. **Menção de terceiros exige revisão** de homônimos e de contexto antes de contar.
12. **Venda irregular, anúncio de produto sem registro e golpe:** registrar e contar, sem repetir links de venda na página pública.

## Decisões do pesquisador

Todas de Wanderson Honorio, em 23/11/2026, por chat.

- A coleta parte de termos de busca e também de perfis confirmados.
- Redes: YouTube, TikTok, Instagram, X e Kwai, além de imprensa, Google Trends e dados públicos.
- Termos: lista ampla mais termos de venda irregular (`data/config/termos.json`).
- Comentários no público: texto anonimizado inteiro. As máscaras estão em `scripts/anonimizar.py` e descritas em `data/config/coleta.json`. A decisão convive com um limite registrado ali: frase longa e incomum ainda pode ser achada pela busca da plataforma. Rever antes da primeira coleta de comentários se o risco mudar.
- A planilha-semente de vídeos do TikTok fica só no repositório privado. As categorias do artigo de referência e os critérios de qualidade viram o livro de códigos (`data/config/livro_de_codigos.json`).
- Marco, janelas e perfis: o levantamento de candidatos é mostrado ao pesquisador, que escolhe. Até lá ficam ⛔.

## Pendências que bloqueiam coleta

- Pergunta de pesquisa e hipóteses: ⛔.
- Marco escolhido e janelas de linha de base e de núcleo: ⛔.
- Perfis confirmados: ⛔.
- Teto e frase de autorização da Apify: sem eles nenhuma coleta paga roda.

## Onde fica cada coisa

| Caminho | O que é |
|---|---|
| `index.html` | Página única. Não tem número escrito à mão: lê `data/config/*.json` e `data/estado.json`. |
| `data/config/` | Recorte, coletas e tetos, termos, perfis, dados públicos e livro de códigos. |
| `data/manifestos/` | Um manifesto por coleta: consulta, universo e fonte, lido, amostra, motivo de parada, custo, arquivos com SHA-256. |
| `data/estado.json` | Resumo dos manifestos, gerado por `scripts/build_estado.py`. Não editar à mão. |
| `scripts/autorizacao.py` | Trava de gasto. |
| `scripts/anonimizar.py` | Anonimização do texto de terceiros antes de ir ao público. |
| `tests/` | Testes das regras acima. |
| `.github/workflows/` | Workflows de disparo manual. Nenhum roda sozinho. |

O repositório privado guarda o bruto de cada coleta, o texto e o autor de terceiros, a planilha-semente, os candidatos a perfil e a tabela que liga autor a código. Os workflows o acessam pelo segredo indicado em `data/config/coleta.json`.

## Antes de cada commit

```
python scripts/build_estado.py
python -m unittest discover -s tests
```

Depois, a entrada no `CHANGELOG.md` no mesmo commit.
