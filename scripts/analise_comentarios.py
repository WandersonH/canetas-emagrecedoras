"""Comentários por rede, no formato dos cadernos de comentários: tom, livro de códigos, aderência ao tema, série
diária, CHD de Reinert, rede de palavras da audiência, quem marca quem e corpus anonimizado para leitura.

Entrada (privado): terceiros/comentarios/<rede>/*.csv, terceiros/<rede>/*.csv (publicações), codigos/autores.json
(gerado por scripts/build_corpus.py no mesmo run) e o cache de tom terceiros/comentarios/sentimento.csv.
Saída (pública, sem nome, perfil, link ou identificador de publicação):
  data/comentarios/<rede>.json         agregados e desenhos das redes
  data/comentarios/<rede>_corpus.json  textos anonimizados (código de autor, data, curtidas, marcas, tom)
  data/redes/comentarios_<rede>_palavras.gexf e comentarios_<rede>_mencoes.gexf
Tom: modelo pysentimiento/bertweet-pt-sentiment (positivo, negativo, neutro), só com --tom e as bibliotecas
instaladas; sem isso, tom fica ⛔. Mede o tom do texto, não a posição sobre o remédio; ironia é lida pelo literal.

Uso:
    python scripts/analise_comentarios.py --privado DIR [--tom]
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import pathlib
import random
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anonimizar  # noqa: E402
import build_corpus  # noqa: E402
import chd_reinert as cr  # noqa: E402
import comum  # noqa: E402
import redes  # noqa: E402

REDES = ("youtube", "tiktok", "instagram", "x")
MODELO = "pysentimiento/bertweet-pt-sentiment"
ROT_TOM = {"POS": "positivo", "NEG": "negativo", "NEU": "neutro"}
MIN_CHD = 500
MAX_CHD = 4000
MENCAO = re.compile(r"(?<![\w@])@([\w.]{2,30})")


def sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


def ler(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def comentarios(privado: pathlib.Path, rede_id: str) -> list[dict]:
    vistos, saida = set(), []
    for caminho in sorted(glob.glob(str(privado / "terceiros" / "comentarios" / rede_id / "*.csv"))):
        for r in ler(caminho):
            if r["comentario_id"] in vistos or not (r.get("texto") or "").strip():
                continue
            vistos.add(r["comentario_id"])
            saida.append(r)
    return sorted(saida, key=lambda r: (r.get("publicado_em") or "", r["comentario_id"]))


def publicacoes(privado: pathlib.Path, rede_id: str) -> dict[str, str]:
    """Texto de cada publicação (título e descrição no YouTube), para a aderência ao tema."""
    textos = {}
    for caminho in sorted(glob.glob(str(privado / "terceiros" / rede_id / "*.csv"))):
        for r in ler(caminho):
            if rede_id == "youtube" and r.get("video_id"):
                textos[r["video_id"]] = f"{r.get('titulo') or ''} {r.get('descricao') or ''}"
            elif r.get("item_id"):
                textos[r["item_id"]] = r.get("texto") or ""
    return textos


def marcas(livro: dict) -> list[tuple[str, str, re.Pattern]]:
    return [(m["id"], m["rotulo"], re.compile("|".join(m["expressoes"]))) for m in livro["marcas"]]


def tema() -> re.Pattern:
    familias = comum.config("termos")["familias"]
    termos = [i["termo"] for k in ("substancias", "marcas", "nomes_populares") for i in familias[k]["itens"]]
    return re.compile("|".join(re.escape(sem_acento(t)) for t in termos + ["caneta", "glp-1", "glp1", "tirze", "sema"]))


# ------------------------------------------------------------------------------------------------ tom


def tom(privado: pathlib.Path, linhas: list[dict], usar_modelo: bool) -> dict[str, str]:
    """Rótulo de tom por comentário, com cache no privado. Sem modelo, devolve só o que já está no cache."""
    cache_arq = privado / "terceiros" / "comentarios" / "sentimento.csv"
    cache = {}
    if cache_arq.exists():
        cache = {r["comentario_id"]: r["rotulo"] for r in ler(str(cache_arq))}
    falta = [r for r in linhas if r["comentario_id"] not in cache]
    if falta and usar_modelo:
        try:
            import emoji
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError:
            print("tom: bibliotecas ausentes; tom fica com o que já estava no cache", flush=True)
            return cache
        tok = AutoTokenizer.from_pretrained(MODELO)
        modelo = AutoModelForSequenceClassification.from_pretrained(MODELO).eval()
        rot = modelo.config.id2label

        def preparar(t):
            t = re.sub(r"https?://\S+|www\.\S+", "url", t or "")
            t = re.sub(r"@[\w.\-]+", "@usuario", t)
            t = emoji.demojize(t, language="pt", delimiters=(" emoji ", " emoji "))
            return re.sub(r"\s+", " ", re.sub(r"(.)\1{3,}", r"\1\1\1", t)).replace("_", " ").strip()
        novos = []
        with torch.inference_mode():
            for i in range(0, len(falta), 64):
                lote = falta[i:i + 64]
                enc = tok([preparar(r["texto"]) for r in lote], padding=True, truncation=True, max_length=128, return_tensors="pt")
                for r, j in zip(lote, modelo(**enc).logits.argmax(-1).tolist()):
                    cache[r["comentario_id"]] = rot[j]
                    novos.append({"comentario_id": r["comentario_id"], "rotulo": rot[j], "modelo": MODELO})
                if i % 3200 == 0:
                    print(f"tom: {i + len(lote)} de {len(falta)}", flush=True)
        existe = cache_arq.exists()
        cache_arq.parent.mkdir(parents=True, exist_ok=True)
        with cache_arq.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["comentario_id", "rotulo", "modelo"])
            if not existe:
                w.writeheader()
            w.writerows(novos)
    return cache


# ------------------------------------------------------------------------------------------------ uma rede


def analisar(rede_id: str, linhas: list[dict], posts: dict[str, str], codigos: dict[str, str], rotulos_tom: dict[str, str],
             ms: list, pat_tema: re.Pattern) -> tuple[dict, list[dict], tuple | None]:
    codigo_post, mencionados = {}, {}

    def cod_autor(a):
        """Código do corpus; quem ficou fora do corpus (comentário em outra língua) ganha código C, só nesta página."""
        chave = (a or "").strip().lower()
        if not chave:
            return ""
        if chave not in codigos:
            codigos[chave] = f"C{sum(1 for v in codigos.values() if v.startswith('C')) + 1:05d}"
        return codigos[chave]

    def cod_mencao(h):
        h = h.lower().rstrip(".")
        if h in codigos:
            return codigos[h]
        return mencionados.setdefault(h, f"M{len(mencionados) + 1:04d}")
    corpus, por_dia, por_mes_tom = [], collections.Counter(), collections.defaultdict(collections.Counter)
    n_marca, curt_marca = collections.Counter(), collections.defaultdict(list)
    tom_total, cita_tema, post_tema = collections.Counter(), 0, 0
    arestas_m = collections.Counter()
    for r in linhas:
        cru = r["texto"]
        sa = sem_acento(cru)
        mk = [i for i, (_, _, p) in enumerate(ms) if p.search(sa)]
        try:
            k = int(float(r.get("curtidas") or 0))
        except ValueError:
            k = None
        for i in mk:
            n_marca[i] += 1
            if k is not None:
                curt_marca[i].append(k)
        t = ROT_TOM.get(rotulos_tom.get(r["comentario_id"], ""), None)
        if t:
            tom_total[t] += 1
        d = (r.get("publicado_em") or "")[:10]
        if d:
            por_dia[d] += 1
            if t:
                por_mes_tom[d[:7]][t] += 1
        if pat_tema.search(sa):
            cita_tema += 1
        if pat_tema.search(sem_acento(posts.get(r["item_id"], ""))):
            post_tema += 1
        autor = cod_autor(r.get("autor"))
        for h in MENCAO.findall(cru):
            alvo = cod_mencao(h)
            if autor and alvo != autor:
                arestas_m[(autor, alvo)] += 1
        corpus.append({"i": len(corpus), "a": autor, "d": d, "k": k, "c": mk, "s": t,
                       "p": codigo_post.setdefault(r["item_id"], f"P{len(codigo_post) + 1:03d}"),
                       "t": anonimizar.anonimizar_texto(cru)})
    n = len(linhas)
    textos_lim = [build_corpus.sem_disfarce(build_corpus.limpar(r["texto"])) for r in linhas]
    nos_p, ar_p, des_p = redes.palavras(textos_lim, minimo=max(5, n // 400), top=110)
    if des_p:
        docs = [set(cr.tokens(t)) for t in textos_lim]
        for no in des_p["nos"]:
            no["seg"] = [i for i, d in enumerate(docs) if no["id"] in d][:400]
    nuvem = sorted(({"forma": k, "n": v["n"]} for k, v in nos_p.items()), key=lambda x: -x["n"])[:90]
    # quem marca quem: autor que comenta -> conta marcada (as duas em código)
    nos_m = {}
    for (a, b), w in arestas_m.items():
        for x in (a, b):
            nos_m.setdefault(x, {"rotulo": x, "tipo": "comentarista" if x.startswith("A") else "marcada", "n": 0})
        nos_m[b]["n"] += w
    des_m = redes._desenho(nos_m, dict(arestas_m), 300, espinha=0) if arestas_m else None
    chd_out = None
    longos = [c for c in corpus if len(c["t"].split()) >= 8]
    if len(longos) >= MIN_CHD:
        random.seed(42)
        amostra = sorted(random.sample(longos, min(MAX_CHD, len(longos))), key=lambda c: c["i"])
        segs = [{"t": c["t"], "doc": c["i"], "f": f"comentario_{rede_id}"} for c in amostra]
        try:
            res, _, _, _ = build_corpus.chd(segs)
            for cl in res["classes"]:  # índices dos segmentos viram índices do corpus da rede
                cl["comentarios_da_classe"] = [amostra[i]["i"] for i in cl.pop("segmentos_da_classe")]
                cl["comentarios_por_forma"] = {f: [amostra[i]["i"] for i in ix] for f, ix in cl.pop("segmentos_por_forma").items()}
                cl.pop("variaveis", None)
            res.pop("arvore", None)
            chd_out = {**res, "amostra": len(amostra), "elegiveis": len(longos)}
        except Exception as erro:  # corpus pequeno demais para dividir
            chd_out = {"erro": f"{type(erro).__name__}: {erro}"[:200], "amostra": len(amostra), "elegiveis": len(longos)}
    agregado = {
        "rede": rede_id, "comentarios": n, "autores_distintos": len({c["a"] for c in corpus if c["a"]}),
        "publicacoes": len(codigo_post), "periodo": [min(por_dia), max(por_dia)] if por_dia else None,
        "tom": {"modelo": MODELO, "classificados": sum(tom_total.values()), "distribuicao": dict(tom_total),
                "por_mes": {m: dict(c) for m, c in sorted(por_mes_tom.items())}} if tom_total else None,
        "marcas": [{"id": ms[i][0], "rotulo": ms[i][1], "n": n_marca[i], "pct": round(100 * n_marca[i] / n, 1) if n else None,
                    "curtidas_medianas": (sorted(curt_marca[i])[len(curt_marca[i]) // 2] if curt_marca[i] else None)}
                   for i in range(len(ms))],
        "aderencia": {"comentarios_que_citam_o_tema": cita_tema, "pct": round(100 * cita_tema / n, 1) if n else None,
                      "comentarios_em_publicacao_que_cita_o_tema": post_tema},
        "por_dia": dict(sorted(por_dia.items())), "nuvem": nuvem, "rede_palavras": des_p, "mencoes": des_m,
        "mencoes_total": sum(arestas_m.values()), "chd": chd_out,
    }
    return agregado, corpus, (nos_p, ar_p, nos_m, dict(arestas_m))


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Comentários por rede.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--tom", action="store_true", help="classifica o tom dos comentários ainda sem rótulo")
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    codigos = comum.carregar(privado / "codigos" / "autores.json") if (privado / "codigos" / "autores.json").exists() else {}
    livro = comum.config("livro_comentarios")
    ms, pat_tema = marcas(livro), tema()
    todos = {r: comentarios(privado, r) for r in REDES}
    rotulos_tom = tom(privado, [c for cs in todos.values() for c in cs], opcoes.tom)
    pasta = comum.RAIZ / "data" / "comentarios"
    indice = {"nota": livro["nota"], "redes": {}}
    for rede_id, linhas in todos.items():
        if not linhas:
            continue
        # mesmo filtro do corpus geral: texto com mais palavras vazias de inglês ou espanhol fica fora da análise
        fora = collections.Counter(build_corpus.idioma(r["texto"]) for r in linhas)
        linhas = [r for r in linhas if build_corpus.idioma(r["texto"]) == "pt"]
        if not linhas:
            continue
        ag, corpus, (nos_p, ar_p, nos_m, ar_m) = analisar(rede_id, linhas, publicacoes(privado, rede_id), codigos, rotulos_tom, ms, pat_tema)
        ag["fora_por_idioma"] = {k: v for k, v in fora.items() if k != "pt"}
        comum.gravar(pasta / f"{rede_id}.json", ag)
        comum.gravar(pasta / f"{rede_id}_corpus.json", corpus)
        if nos_p:
            redes.gexf(nos_p, ar_p, comum.RAIZ / "data" / "redes" / f"comentarios_{rede_id}_palavras.gexf")
        if nos_m:
            redes.gexf(nos_m, ar_m, comum.RAIZ / "data" / "redes" / f"comentarios_{rede_id}_mencoes.gexf")
        indice["redes"][rede_id] = {"comentarios": ag["comentarios"], "tom_classificados": (ag["tom"] or {}).get("classificados")}
        print(f"comentarios {rede_id}: {ag['comentarios']} comentários, {ag['autores_distintos']} autores, "
              f"tom {(ag['tom'] or {}).get('classificados', '⛔')}, CHD {'sim' if ag['chd'] and 'classes' in ag['chd'] else 'não'}", flush=True)
    comum.gravar(pasta / "analise.json", indice)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
