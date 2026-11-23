"""Chamadas à Apify.

Não existe aqui consulta de saldo nem de limites da conta. O gasto é controlado pelo teto de cada execução
(maxTotalChargeUsd) e pela soma dos custos gravados nos manifestos (scripts/autorizacao.py).
O token vem só de variável de ambiente e nunca é gravado nem impresso.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

API = "https://api.apify.com/v2"


def api(metodo: str, caminho: str, token: str, corpo=None, tempo: int = 360):
    pedido = urllib.request.Request(f"{API}{caminho}", method=metodo,
                                    data=None if corpo is None else json.dumps(corpo).encode(),
                                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
        return json.loads(resposta.read() or b"null")


def baixar_itens(token: str, dataset: str, pagina: int = 500) -> list:
    itens, inicio = [], 0
    while True:
        for tentativa in range(4):
            try:
                lote = api("GET", f"/datasets/{dataset}/items?clean=true&format=json&limit={pagina}&offset={inicio}", token) or []
                break
            except Exception:
                if tentativa == 3:
                    raise
                time.sleep(5 * (tentativa + 1))
        itens += lote
        if len(lote) < pagina:
            return itens
        inicio += pagina


ESPERA_MAXIMA_S = 900


def rodar(token: str, ator: str, entrada: dict, teto_usd: float, espera_maxima_s: int = ESPERA_MAXIMA_S) -> tuple[dict, list]:
    """Roda o ator com teto de cobrança e devolve (execução, itens).
    Se a execução passar de espera_maxima_s, é abortada e o que ela já coletou é aproveitado."""
    run = api("POST", f"/acts/{ator}/runs?waitForFinish=60&maxTotalChargeUsd={teto_usd}", token, entrada)["data"]
    inicio = time.monotonic()
    while run.get("status") in ("READY", "RUNNING"):
        if time.monotonic() - inicio > espera_maxima_s:
            api("POST", f"/actor-runs/{run['id']}/abort", token)
            time.sleep(10)
            run = api("GET", f"/actor-runs/{run['id']}", token)["data"]
            break
        run = api("GET", f"/actor-runs/{run['id']}?waitForFinish=60", token)["data"]
    for espera in (5, 10, 20):  # a cobrança aparece na execução alguns segundos depois de terminar
        if run.get("usageTotalUsd") or run.get("chargedEventCounts"):
            break
        time.sleep(espera)
        run = api("GET", f"/actor-runs/{run['id']}", token)["data"]
    return run, baixar_itens(token, run["defaultDatasetId"])


def custo(run: dict) -> float:
    """Custo cobrado na execução: eventos × preço do evento; sem eventos, usageTotalUsd."""
    eventos = ((run.get("pricingInfo") or {}).get("pricingPerEvent") or {}).get("actorChargeEvents") or {}
    total = 0.0
    for nome, quantidade in (run.get("chargedEventCounts") or {}).items():
        evento = eventos.get(nome) or {}
        preco = evento.get("eventPriceUsd")
        if preco is None:
            preco = ((evento.get("eventTieredPricingUsd") or {}).get("FREE") or {}).get("tieredEventPriceUsd") or 0
        total += float(quantidade or 0) * float(preco or 0)
    return round(total or float(run.get("usageTotalUsd") or 0), 5)


def erro_curto(erro: Exception) -> str:
    texto = f"{type(erro).__name__} {getattr(erro, 'code', '')}".strip()
    if isinstance(erro, urllib.error.HTTPError):
        try:
            detalhe = (json.loads(erro.read() or b"{}") or {}).get("error") or {}
            texto += f" {detalhe.get('type')}: {str(detalhe.get('message'))[:160]}"
        except Exception:
            pass
    return texto[:240]
