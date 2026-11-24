"""Agregados da codificação manual JAMA da planilha-semente (repositório privado).

Lê a aba de análise, conta cada vídeo uma vez por endereço e grava só agregados em
data/jama/manual.json: nenhum nome, perfil, link, legenda, transcrição ou justificativa.

Uso: python scripts/resumo_jama.py --privado DIR
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402


def grupo(valor, grupos: dict) -> str:
    v = (str(valor).strip() if valor is not None else "")
    for g, rotulos in grupos.items():
        if v in rotulos:
            return g
    return "sem rótulo" if not v or v == "None" else "outro rótulo"


def ponto(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def resumir(linhas: list[dict], cfg: dict, ids_coletados: set[str]) -> dict:
    vistos, vids = set(), []
    for r in linhas:
        u = (r.get("URL") or "").strip()
        if not u or u in vistos:
            continue
        vistos.add(u)
        vids.append(r)
    n = len(vids)
    crit = cfg["criterios"]
    pts = {c["id"]: [ponto(v.get(c["coluna"])) for v in vids] for c in crit}
    score = [ponto(v.get(cfg["coluna_pontuacao"])) for v in vids]
    soma_confere = sum(1 for i, s in enumerate(score) if s is not None and s == sum(pts[c["id"]][i] or 0 for c in crit))
    gp, gc = cfg["tipo_de_perfil"]["grupos"], cfg["tipo_de_caneta"]["grupos"]

    def por(dim_grupos, coluna):
        acc = collections.defaultdict(list)
        for i, v in enumerate(vids):
            acc[grupo(v.get(coluna), dim_grupos)].append(i)
        out = []
        for g, ix in sorted(acc.items(), key=lambda x: -len(x[1])):
            sc = [score[i] for i in ix if score[i] is not None]
            out.append({"grupo": g, "videos": len(ix), "pontuacao_media": round(sum(sc) / len(sc), 2) if sc else None,
                        **{c["id"]: pct(sum(1 for i in ix if pts[c["id"]][i] == 1), len(ix)) for c in crit}})
        return out

    datas = sorted(str(v.get("Data"))[:10] for v in vids if str(v.get("Data") or "")[:4].isdigit())
    ids = set()
    for v in vids:
        achado = re.search(r"/video/(\d+)", str(v.get("URL") or ""))
        i = str(v.get("ID do vídeo") or "").strip() or (achado.group(1) if achado else "")
        if i:
            ids.add(i)
    validos = [s for s in score if s is not None]
    return {
        "linhas_na_planilha": len(linhas), "videos": n, "linhas_repetidas": len(linhas) - n,
        "unidade": cfg["unidade"],
        "criterios": [{"id": c["id"], "rotulo": c["rotulo"], "presente": sum(1 for x in pts[c["id"]] if x == 1),
                       "ausente": sum(1 for x in pts[c["id"]] if x == 0), "sem_valor": sum(1 for x in pts[c["id"]] if x is None),
                       "pct": pct(sum(1 for x in pts[c["id"]] if x == 1), n)} for c in crit],
        "pontuacao": {"distribuicao": {str(k): validos.count(k) for k in range(5)},
                      "media": round(sum(validos) / len(validos), 2) if validos else None,
                      "soma_confere": soma_confere, "sem_valor": n - len(validos)},
        "por_tipo_de_perfil": por(gp, "Tipo de perfil"),
        "por_tipo_de_caneta": por(gc, "Tipo de caneta"),
        "rotulos_distintos": {k: len({str(v.get(k)).strip() for v in vids}) for k in ("Tipo de perfil", "Tipo de caneta", "Tipo de conteúdo")},
        "datas": {"com_data": len(datas), "primeira": datas[0] if datas else None, "ultima": datas[-1] if datas else None},
        "com_id": len(ids), "na_coleta_do_projeto": len(ids & ids_coletados),
    }


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description=__doc__)
    leitor.add_argument("--privado", required=True)
    op = leitor.parse_args(argumentos)
    privado = pathlib.Path(op.privado)
    cfg = comum.config("jama")
    arq = privado / cfg["semente"]
    if not arq.exists():
        print(f"⛔ planilha-semente não encontrada em {cfg['semente']}")
        return 1
    import openpyxl
    ws = openpyxl.load_workbook(arq, data_only=True)[cfg["aba"]]
    rows = list(ws.iter_rows(values_only=True))
    cab = [str(c).strip() if c is not None else "" for c in rows[0]]
    linhas = [dict(zip(cab, r)) for r in rows[1:] if any(x is not None for x in r)]
    aba_resumo = None  # a aba Resumo da planilha declara o total analisado; comparado com a aba principal
    if "Resumo" in ws.parent.sheetnames:
        for r in ws.parent["Resumo"].iter_rows(values_only=True):
            if r and str(r[0] or "").startswith("Vídeos transcritos e analisados"):
                aba_resumo = ponto(r[1])
    coletados = set()
    for f in glob.glob(str(privado / "terceiros" / "tiktok" / "*.csv")):
        coletados.update(x for x in pathlib.Path(f).read_text(encoding="utf-8", errors="ignore").replace(",", " ").split() if x.isdigit() and len(x) >= 18)
    saida = {"nota": cfg["nota"], "fonte": "codificação manual do grupo de pesquisadores, planilha-semente no repositório privado",
             "sha256": hashlib.sha256(arq.read_bytes()).hexdigest(), "obtido_em": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             **resumir(linhas, cfg, coletados), "aba_resumo_declara": aba_resumo, "ia": cfg["ia"]}
    comum.gravar(comum.RAIZ / "data" / "jama" / "manual.json", saida)
    print(f"jama: {saida['videos']} vídeos ({saida['linhas_na_planilha']} linhas), média {saida['pontuacao']['media']}, na coleta {saida['na_coleta_do_projeto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
