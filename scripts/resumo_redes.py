"""Converte as estatísticas das redes (CSV do scripts/estatisticas_redes.py) em JSON para a página.

Uso: python scripts/resumo_redes.py
"""
from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

CAMPOS = ["rede", "dirigida", "nos", "arestas", "densidade", "grau_medio", "grau_ponderado_medio", "componentes",
          "pct_nos_maior_componente", "clustering_medio", "assortatividade_grau", "reciprocidade", "diametro_maior_componente",
          "caminho_medio_maior_componente", "modularidade_q", "comunidades", "comunidades_1pct_ou_mais", "pct_maior",
          "pct_segunda", "pct_terceira", "ei_duas_maiores", "gc_modularidade_q", "gc_comunidades_1pct_ou_mais",
          "gc_polarizacao_ei_2_maiores"]


def numero(v):
    """Texto do CSV para número; vazio fica None (⛔ na página), nunca zero."""
    if v in (None, ""):
        return None
    if v in ("True", "False"):
        return v == "True"
    try:
        f = float(v)
        if f != f or f in (float("inf"), float("-inf")):  # NaN e infinito: medida indefinida, fica ⛔
            return None
        return int(f) if f.is_integer() and "." not in v and "e" not in v.lower() else f
    except ValueError:
        return v


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
             "redes": [{k: (l.get(k) if k == "rede" else numero(l.get(k))) for k in CAMPOS} for l in est],
             "comunidades": [{k: (v if k in ("caso", "rede", "nos_de_maior_grau") else numero(v)) for k, v in c.items()}
                             for c in ler(pasta / "comunidades_redes.csv")],
             "centralidades": [{k: (v if k in ("caso", "rede", "medida", "no") else numero(v)) for k, v in c.items()}
                               for c in ler(pasta / "centralidades_redes.csv")]}
    comum.gravar(pasta / "estatisticas.json", saida)
    print(f"gravado data/redes/estatisticas.json: {len(est)} redes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
