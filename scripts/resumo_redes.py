"""Converte as estatísticas das redes (CSV do scripts/estatisticas_redes.py) em JSON para a página.

Uso: python scripts/resumo_redes.py
"""
from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

CAMPOS = ["rede", "nos", "arestas", "densidade", "grau_medio", "componentes", "pct_nos_maior_componente", "clustering_medio",
          "modularidade_q", "comunidades", "comunidades_1pct_ou_mais", "pct_maior", "pct_segunda", "pct_terceira",
          "ei_duas_maiores", "diametro_maior_componente", "caminho_medio_maior_componente"]


def ler(caminho: pathlib.Path) -> list[dict]:
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def main() -> int:
    pasta = comum.RAIZ / "data" / "redes"
    est = ler(pasta / "estatisticas_redes.csv")
    for linha in est:  # o índice E-I das duas maiores comunidades vem com nome próprio no CSV
        linha["ei_duas_maiores"] = linha.get("polarizacao_ei_2_maiores")
    saida = {"nota": "Medidas do painel Statistics do Gephi. Modularidade por Louvain (resolução 1,0, semente 42). "
                     "E-I entre as duas maiores comunidades: −1 = duas bolhas sem contato; +1 = só contato cruzado.",
             "redes": [{k: l.get(k) for k in CAMPOS} for l in est],
             "comunidades": ler(pasta / "comunidades_redes.csv")}
    comum.gravar(pasta / "estatisticas.json", saida)
    print(f"gravado data/redes/estatisticas.json: {len(est)} redes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
