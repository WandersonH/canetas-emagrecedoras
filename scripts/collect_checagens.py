"""Checagens publicadas pelas agências sobre as canetas emagrecedoras: Google Fact Check Tools API (sem custo).

Fonte: claims:search, que reúne checagens no formato ClaimReview. O estudo não dá veredito: mostra o que cada agência
checou, com o rótulo dela, a data e o link.

Chave: FACTCHECK_API_KEY; sem ela, YOUTUBE_API_KEY (funciona se a Fact Check Tools API estiver ativa no mesmo
projeto do Google Cloud). Recusa da chave é registrada como bloqueio.

A API só filtra por idade (maxAgeDays, contada a partir de hoje). O coletor pede desde o início do período lido e
descarta o que tiver data de checagem anterior a ele.

Universo: a API não informa quantas checagens existem (⛔).
Saída pública: data/checagens/checagens.json. Quem fez a alegação (claimant) é omitido: pode ser pessoa comum.

Uso:
    python scripts/collect_checagens.py --run-id 123
"""
from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402

URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
MAX_PAGINAS = 3


def buscar(chave: str, termo: str, dias: int, leitor=rede.pegar_json) -> tuple[list[dict], str]:
    itens, token, parou = [], None, "fim_dos_resultados"
    for numero in range(MAX_PAGINAS):
        parametros = {"query": termo, "languageCode": "pt", "maxAgeDays": dias, "pageSize": 100, "key": chave}
        if token:
            parametros["pageToken"] = token
        resposta = leitor(f"{URL}?{urllib.parse.urlencode(parametros)}")
        itens += resposta.get("claims", [])
        token = resposta.get("nextPageToken")
        if not token:
            break
    else:
        parou = "limite"
    return itens, parou


def normalizar(claims: list[tuple[str, dict]], inicio: datetime.date) -> list[dict]:
    """Uma linha por checagem (link da agência), com os termos que a trouxeram. Sem claimant."""
    por_link: dict[str, dict] = {}
    for termo, claim in claims:
        for revisao in claim.get("claimReview") or []:
            link = revisao.get("url")
            data = (revisao.get("reviewDate") or claim.get("claimDate") or "")[:10]
            if not link or not data or data < inicio.isoformat():
                continue
            linha = por_link.setdefault(link, {
                "alegacao": claim.get("text"), "agencia": (revisao.get("publisher") or {}).get("name"),
                "site": (revisao.get("publisher") or {}).get("site"), "rotulo": revisao.get("textualRating"),
                "titulo": revisao.get("title"), "data": data, "idioma": revisao.get("languageCode"), "link": link,
                "termos": []})
            if termo not in linha["termos"]:
                linha["termos"].append(termo)
    return sorted(por_link.values(), key=lambda x: (x["data"], x["link"]), reverse=True)


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Checagens publicadas sobre o tema.")
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    chave = os.environ.get("FACTCHECK_API_KEY") or os.environ.get("YOUTUBE_API_KEY") or ""
    inicio, fim = rede.periodo_lido()
    dias = (datetime.datetime.now(datetime.timezone.utc).date() - inicio).days + 1
    termos = rede.termos_de_busca()
    manifesto = rede.Manifesto("checagens", {"termos": [t["termo"] for t in termos], "inicio": inicio.isoformat(),
                                             "fim": fim.isoformat(), "idioma": "pt", "max_paginas_por_termo": MAX_PAGINAS},
                               opcoes.run_id)
    if not chave:
        manifesto.bloqueio("sem chave (FACTCHECK_API_KEY ou YOUTUBE_API_KEY)")
        manifesto.gravar()
        print("BLOQUEADO: sem chave")
        return 1
    coletados, lidos, paradas = [], 0, []
    for t in termos:
        try:
            itens, parou = buscar(chave, t["termo"], dias)
        except Exception as erro:
            manifesto.bloqueio(f"'{t['termo']}': {type(erro).__name__}: {erro}")
            continue
        lidos += len(itens)
        paradas.append(parou)
        coletados += [(t["termo"], c) for c in itens]
        print(f"{t['termo']}: {len(itens)} alegações lidas")
    checagens = normalizar(coletados, inicio)
    destino = comum.RAIZ / "data" / "checagens" / "checagens.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
                           "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
                           "nota": "Rótulo e texto são das agências. Quem fez a alegação é omitido.",
                           "checagens": checagens})
    manifesto.arquivo(destino, comum.RAIZ)
    consultou = bool(paradas)
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "A Fact Check Tools API não informa quantas checagens existem."},
        "lido": lidos if consultou else None,
        "amostra": {"n": len(checagens) if consultou else None,
                    "como": "checagens distintas (link da agência) com data dentro do período lido"},
        "parou_por": ("limite" if "limite" in paradas else "fim_dos_resultados") if consultou else None,
    })
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {len(checagens)} checagens no período")
    return 0 if consultou else 1


if __name__ == "__main__":
    raise SystemExit(main())
