"""Proposições da Câmara dos Deputados sobre as canetas emagrecedoras (API de dados abertos, sem custo).

Fonte: https://dadosabertos.camara.leg.br/api/v2/proposicoes, com keywords = cada termo de busca e substância,
apresentadas a partir do início do período lido. A API informa o total de cada consulta no cabeçalho
x-total-count: esse é o universo da consulta.

Saída pública: data/dados_publicos/camara.json (proposições são documentos públicos do Legislativo).

Uso:
    python scripts/collect_camara.py --run-id 123
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402

URL = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
POR_PAGINA = 100
MAX_PAGINAS = 10


def palavras(raiz: pathlib.Path | None = None) -> list[str]:
    familias = comum.config("termos", raiz)["familias"]
    saida = [i["termo"] for i in familias["substancias"]["itens"]]
    saida += [t["termo"] for t in rede.termos_de_busca(raiz) if t["termo"] not in saida]
    return saida


def pedir(url: str, tentativas: int = 3) -> tuple[dict, int | None]:
    pedido = urllib.request.Request(url, headers={"User-Agent": rede.AGENTE, "Accept": "application/json"})
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                total = resposta.headers.get("x-total-count")
                return json.loads(resposta.read()), int(total) if total and total.isdigit() else None
        except Exception:
            if tentativa == tentativas - 1:
                raise
            time.sleep(5 * (tentativa + 1))
    raise RuntimeError("inalcançável")


def consultar(termo: str, inicio: str, fim: str, leitor=pedir) -> tuple[list[dict], int | None, str]:
    itens, total, parou = [], None, "fim_dos_resultados"
    for pagina in range(1, MAX_PAGINAS + 1):
        q = {"keywords": termo, "dataApresentacaoInicio": inicio, "dataApresentacaoFim": fim, "itens": POR_PAGINA,
             "pagina": pagina, "ordem": "DESC", "ordenarPor": "id"}
        corpo, t = leitor(f"{URL}?{urllib.parse.urlencode(q)}")
        total = t if t is not None else total
        lote = corpo.get("dados") or []
        itens += lote
        if len(lote) < POR_PAGINA:
            break
    else:
        parou = "limite"
    return itens, total, parou


def main(argumentos=None, leitor=pedir, raiz: pathlib.Path | None = None) -> int:
    opcoes = argparse.ArgumentParser(description="Proposições da Câmara sobre o tema.")
    opcoes.add_argument("--run-id", default=None)
    opcoes = opcoes.parse_args(argumentos)
    raiz = raiz or comum.RAIZ
    inicio, fim = (d.isoformat() for d in rede.periodo_lido(raiz))
    termos = palavras(raiz)
    manifesto = rede.Manifesto("dados_publicos", {"subfrente": "camara", "fonte": URL, "termos": termos,
                                                  "inicio": inicio, "fim": fim, "por_pagina": POR_PAGINA,
                                                  "max_paginas": MAX_PAGINAS}, opcoes.run_id)
    por_id, consultas = {}, []
    for termo in termos:
        try:
            itens, total, parou = consultar(termo, inicio, fim, leitor)
        except Exception as erro:
            manifesto.bloqueio(f"'{termo}': {type(erro).__name__}: {erro}")
            consultas.append({"termo": termo, "total_informado": None, "lidos": None, "parou_por": None})
            continue
        consultas.append({"termo": termo, "total_informado": total, "lidos": len(itens), "parou_por": parou})
        for p in itens:
            linha = por_id.setdefault(p["id"], {"id": p["id"], "tipo": p.get("siglaTipo"), "numero": p.get("numero"),
                                                "ano": p.get("ano"), "ementa": p.get("ementa"),
                                                "link": f"https://www.camara.leg.br/propostas-legislativas/{p['id']}",
                                                "termos": []})
            linha["termos"].append(termo)
        print(f"camara '{termo}': {len(itens)} de {total} informadas", flush=True)
    proposicoes = sorted(por_id.values(), key=lambda p: -int(p["id"]))
    por_tipo: dict[str, int] = {}
    for p in proposicoes:
        por_tipo[p["tipo"] or "não informado"] = por_tipo.get(p["tipo"] or "não informado", 0) + 1
    destino = raiz / "data" / "dados_publicos" / "camara.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
                           "periodo": {"inicio": inicio, "fim": fim},
                           "nota": "Proposições apresentadas no período cuja busca por palavra-chave da Câmara devolve o termo.",
                           "consultas": consultas, "por_tipo": por_tipo, "proposicoes": proposicoes})
    manifesto.arquivo(destino, raiz)
    respondidas = [c for c in consultas if c["lidos"] is not None]
    totais = [c["total_informado"] for c in respondidas if c["total_informado"] is not None]
    manifesto.dados.update({
        "universo": {"valor": sum(totais) if respondidas and len(totais) == len(respondidas) else None,
                     "fonte": "soma do x-total-count de cada consulta (as consultas se sobrepõem)"},
        "lido": sum(c["lidos"] for c in respondidas) if respondidas else None,
        "amostra": {"n": len(proposicoes) if respondidas else None, "como": "proposições distintas"},
        "parou_por": ("limite" if any(c["parou_por"] == "limite" for c in respondidas) else "fim_dos_resultados") if respondidas else None})
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: camara, {len(proposicoes)} proposições")
    return 0 if respondidas else 1


if __name__ == "__main__":
    raise SystemExit(main())
