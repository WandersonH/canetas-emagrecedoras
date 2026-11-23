# Canetas emagrecedoras

Estudo sobre como as canetas emagrecedoras (agonistas de GLP-1) aparecem nas redes, na imprensa e nas buscas no Brasil: promessa, risco, uso sem prescrição e venda irregular.

**Situação:** estrutura montada, nenhuma coleta executada. Todo dado da página está como ⛔.

## Como o projeto trata os dados

- Todo número vem de arquivo, manifesto ou execução identificável. Dado ausente é ⛔, nunca zero.
- Toda amostra aparece ao lado do universo que a plataforma informa, de quanto foi lido e de como foi tirada.
- Só perfil confirmado é coletado.
- Na página pública entram as publicações dos perfis monitorados e os agregados. Texto e autor de terceiros ficam em repositório privado. Relato de uso, peso, doença ou efeito colateral de pessoa comum é dado sensível.
- Venda irregular é registrada e contada, sem repetir links de venda.
- Coleta paga só roda com teto e frase de autorização gravados na configuração.

As regras completas estão em [`CLAUDE.md`](CLAUDE.md) e o histórico em [`CHANGELOG.md`](CHANGELOG.md).

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `index.html` | Página do estudo |
| `data/config/` | Recorte, coletas, termos, perfis, dados públicos, livro de códigos |
| `data/manifestos/` | Um manifesto por coleta |
| `data/estado.json` | Resumo das coletas, gerado por script |
| `scripts/` | Trava de gasto, anonimização e resumo das coletas |
| `tests/` | Testes das regras do projeto |

## Rodar os testes

```
python scripts/build_estado.py
python -m unittest discover -s tests
```

Só usa a biblioteca padrão do Python.

## Ver a página no computador

```
python -m http.server 8000
```

Depois abra `http://localhost:8000`. A página lê arquivos de dados e não funciona aberta direto do disco.
