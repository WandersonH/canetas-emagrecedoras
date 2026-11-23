"""Trava de gasto: coleta paga só roda com teto e frase de autorização gravados.

Regras, todas lidas de data/config/coleta.json e dos manifestos:
- o teto total da Apify tem de ser maior que zero;
- a frase de autorização (quem, quando, o quê) não pode estar vazia;
- a etapa pedida tem de existir e ter teto maior que zero;
- a soma dos tetos das etapas não pode passar do teto total;
- o gasto já feito na etapa (somado dos manifestos) mais o previsto não pode passar do teto da etapa.

Este módulo nunca consulta saldo nem limites da conta.

Uso em workflow, antes de qualquer chamada paga:
    python scripts/autorizacao.py --etapa teste --previsto 0.50
Sai com código 0 quando pode rodar e com código 1, explicando o motivo, quando não pode.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402


class GastoNaoAutorizado(Exception):
    """A coleta paga não pode rodar."""


def gasto_da_etapa(etapa: str, pasta_manifestos: pathlib.Path | None = None) -> float:
    """Soma o custo, em dólares, dos manifestos já gravados para a etapa."""
    pasta = pasta_manifestos or comum.MANIFESTOS
    total = 0.0
    if not pasta.exists():
        return total
    for caminho in sorted(pasta.glob("*.json")):
        manifesto = comum.carregar(caminho)
        if manifesto.get("etapa") == etapa:
            total += float(manifesto.get("custo_usd") or 0)
    return total


def verificar(apify: dict, etapa: str, previsto_usd: float, ja_gasto_usd: float = 0.0) -> float:
    """Confere as regras e devolve quanto ainda sobra na etapa depois do gasto previsto."""
    teto_total = float(apify.get("teto_usd") or 0)
    if teto_total <= 0:
        raise GastoNaoAutorizado("teto total da Apify é zero: nenhuma coleta paga está autorizada")
    if not str(apify.get("autorizacao") or "").strip():
        raise GastoNaoAutorizado("frase de autorização vazia: falta gravar quem autorizou, quando e o quê")
    etapas = apify.get("etapas") or {}
    if etapa not in etapas:
        raise GastoNaoAutorizado(f"etapa desconhecida: {etapa}")
    teto_etapa = float(etapas[etapa] or 0)
    if teto_etapa <= 0:
        raise GastoNaoAutorizado(f"teto da etapa '{etapa}' é zero")
    soma_etapas = sum(float(valor or 0) for valor in etapas.values())
    if soma_etapas > teto_total + 1e-9:
        raise GastoNaoAutorizado("a soma dos tetos das etapas passa do teto total")
    if previsto_usd < 0 or ja_gasto_usd < 0:
        raise GastoNaoAutorizado("valor de gasto negativo")
    if ja_gasto_usd + previsto_usd > teto_etapa + 1e-9:
        raise GastoNaoAutorizado(
            f"a etapa '{etapa}' passaria do teto: gasto já feito mais o previsto é maior que o teto da etapa"
        )
    return teto_etapa - ja_gasto_usd - previsto_usd


def main(argumentos: list[str] | None = None) -> int:
    leitor = argparse.ArgumentParser(description="Confere se uma coleta paga pode rodar.")
    leitor.add_argument("--etapa", required=True)
    leitor.add_argument("--previsto", type=float, required=True, help="gasto previsto em dólares")
    opcoes = leitor.parse_args(argumentos)
    apify = comum.config("coleta")["apify"]
    try:
        verificar(apify, opcoes.etapa, opcoes.previsto, gasto_da_etapa(opcoes.etapa))
    except GastoNaoAutorizado as erro:
        print(f"BLOQUEADO: {erro}")
        return 1
    print(f"AUTORIZADO: etapa '{opcoes.etapa}' dentro do teto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
