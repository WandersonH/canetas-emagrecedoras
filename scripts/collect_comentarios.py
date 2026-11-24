"""Comentários das publicações já coletadas: YouTube (Data API, sem custo) e TikTok, Instagram e X (Apify, etapa
"comentarios" de data/config/coleta.json).

Quais publicações: as já coletadas no período lido (repositório privado, terceiros/<rede>/), ordenadas pelo número
de comentários que a própria rede informa; entram as N primeiras de cada rede (data/config/coleta.json,
"comentarios"). Isso é uma amostra intencional das publicações com mais conversa, não do universo.

Universo: soma dos comentários que cada rede informa nas publicações escolhidas (o contador público da rede).
Lido: comentários devolvidos. Amostra: comentários distintos com texto.

Privacidade: texto e autor dos comentários ficam só no repositório privado (terceiros/comentarios/<rede>/).
No público, os textos entram anonimizados pelo corpus (scripts/build_corpus.py); aqui só contagens.

Uso:
    python scripts/collect_comentarios.py --privado DIR --redes youtube tiktok instagram x --run-id 123
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apify  # noqa: E402
import autorizacao  # noqa: E402
import collect_redes  # noqa: E402
import collect_youtube_historico as historico  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

ETAPA = "comentarios"
CAMPOS = ["rede", "comentario_id", "item_id", "autor", "publicado_em", "texto", "curtidas", "respostas"]
YT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
PADRAO = {"youtube": {"publicacoes": 300, "por_publicacao": 100},
          "tiktok": {"ator": "clockworks~tiktok-comments-scraper", "preco_item": 0.001, "publicacoes": 40, "por_publicacao": 25},
          "instagram": {"ator": "apify~instagram-comment-scraper", "preco_item": 0.0023, "publicacoes": 15, "por_publicacao": 20},
          "x": {"ator": "xquik~x-tweet-scraper", "preco_item": 0.00015, "publicacoes": 40, "por_publicacao": 25}}


def configuracao(coleta: dict) -> dict:
    cfg = {k: dict(v) for k, v in PADRAO.items()}
    for k, v in (coleta.get("comentarios") or {}).items():
        if k in cfg and isinstance(v, dict):
            cfg[k].update(v)
    return cfg


def ler_csv(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def escolher(privado: pathlib.Path, rede_id: str, n: int, inicio: str, fim: str) -> list[dict]:
    """As n publicações do período com mais comentários informados, sem repetição."""
    por_id: dict[str, dict] = {}
    if rede_id == "youtube":
        for caminho in sorted(glob.glob(str(privado / "terceiros" / "youtube" / "*.csv"))):
            for r in ler_csv(caminho):
                if r.get("video_id"):
                    por_id[r["video_id"]] = {"item_id": r["video_id"], "data": (r.get("publicado_em") or "")[:10],
                                             "comentarios": collect_redes.inteiro(r.get("comentarios")),
                                             "url": f"https://www.youtube.com/watch?v={r['video_id']}",
                                             "texto": f"{r.get('titulo') or ''}"}
    else:
        for caminho in sorted(glob.glob(str(privado / "terceiros" / rede_id / "*.csv"))):
            if "/teste_" in caminho.replace("\\", "/"):
                continue
            for r in ler_csv(caminho):
                if r.get("item_id"):
                    por_id[r["item_id"]] = {"item_id": r["item_id"], "data": (r.get("publicado_em") or "")[:10],
                                            "comentarios": collect_redes.inteiro(r.get("comentarios")), "url": r.get("url"),
                                            "texto": r.get("texto") or ""}
    candidatas = [p for p in por_id.values() if p["data"] and inicio <= p["data"] <= fim and (p["comentarios"] or 0) > 0
                  and (rede_id == "youtube" or p["url"])]
    if rede_id == "youtube":  # só vídeos em português: o título decide
        candidatas = [p for p in candidatas if _portugues(p["texto"])]
    return sorted(candidatas, key=lambda p: (-(p["comentarios"] or 0), p["item_id"]))[:n]


def _portugues(texto: str) -> bool:
    import re
    ws = re.findall(r"[a-záéíóúâêôãõçñü]+", (texto or "").lower())
    pt = sum(w in {"de", "do", "da", "que", "com", "para", "não", "é", "o", "a", "os", "as", "um", "uma", "em", "no", "na",
                   "caneta", "emagrecer", "emagrecedora", "você", "como"} for w in ws)
    es = sum(w in {"el", "la", "los", "las", "del", "y", "para", "bajar", "peso", "cómo", "qué", "adelgazar"} for w in ws)
    en = sum(w in {"the", "and", "of", "to", "how", "weight", "loss", "my", "is", "for", "what"} for w in ws)
    return pt >= es and pt >= en


# ------------------------------------------------------------------------------------------------ YouTube


def youtube(chave: str, publicacoes: list[dict], por_publicacao: int, leitor=rede.pegar_json) -> tuple[list[dict], dict]:
    linhas, registro = [], {"pedidas": len(publicacoes), "respondidas": 0, "fechadas": 0, "cota_esgotada": False, "erros": 0}
    for p in publicacoes:
        parametros = {"part": "snippet", "videoId": p["item_id"], "maxResults": min(100, por_publicacao),
                      "order": "relevance", "textFormat": "plainText", "key": chave}
        try:
            r = leitor(f"{YT_URL}?{urllib.parse.urlencode(parametros)}", tentativas=2, tempo=30)
        except Exception as erro:
            if historico.cota(erro):
                registro["cota_esgotada"] = True
                break
            if isinstance(erro, urllib.error.HTTPError) and erro.code == 403:
                registro["fechadas"] += 1  # comentários desativados no vídeo
                continue
            registro["erros"] += 1
            continue
        registro["respondidas"] += 1
        for item in r.get("items", []):
            s = ((item.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {}
            linhas.append({"rede": "youtube", "comentario_id": item.get("id"), "item_id": p["item_id"],
                           "autor": (s.get("authorChannelId") or {}).get("value") or s.get("authorDisplayName") or "",
                           "publicado_em": (s.get("publishedAt") or "")[:10], "texto": " ".join((s.get("textDisplay") or "").split()),
                           "curtidas": s.get("likeCount"), "respostas": (item.get("snippet") or {}).get("totalReplyCount")})
    return linhas, registro


# ------------------------------------------------------------------------------------------------ Apify


def entrada(rede_id: str, publicacoes: list[dict], por_publicacao: int) -> dict:
    urls = [p["url"] for p in publicacoes]
    if rede_id == "tiktok":
        return {"postURLs": urls, "commentsPerPost": por_publicacao, "maxRepliesPerComment": 0}
    if rede_id == "instagram":
        return {"directUrls": urls, "resultsLimit": por_publicacao}
    if rede_id == "x":
        return {"searchTerms": [f"conversation_id:{p['item_id']}" for p in publicacoes],
                "maxItems": por_publicacao * len(publicacoes), "queryType": "Latest"}
    raise ValueError(rede_id)


def normalizar(rede_id: str, x: dict, alvo: set[str]) -> dict | None:
    g = collect_redes.g
    if x.get("error") or x.get("noResults") or x.get("demo"):
        return None
    if rede_id == "tiktok":
        iid = g(x, "cid", "id", "commentId")
        post = str(g(x, "videoWebUrl", "aweme_id", "awemeId", "videoId", "postId") or "")
        autor = g(x, "uniqueId", "user.uniqueId", "author.uniqueId", "username")
        linha = {"publicado_em": collect_redes.data_iso(g(x, "createTimeISO", "createTime", "create_time")),
                 "texto": g(x, "text", "comment"), "curtidas": collect_redes.inteiro(g(x, "diggCount", "likes", "likeCount")),
                 "respostas": collect_redes.inteiro(g(x, "replyCommentTotal", "replyCount", "replies"))}
    elif rede_id == "instagram":
        iid = g(x, "id", "pk")
        post = str(g(x, "postUrl", "post.url", "inputUrl", "shortCode", "postId") or "")
        autor = g(x, "ownerUsername", "owner.username", "user.username", "username")
        linha = {"publicado_em": collect_redes.data_iso(g(x, "timestamp", "createdAt", "created_at")),
                 "texto": g(x, "text", "comment"), "curtidas": collect_redes.inteiro(g(x, "likesCount", "likeCount")),
                 "respostas": collect_redes.inteiro(g(x, "repliesCount", "replyCount"))}
    elif rede_id == "x":
        iid = g(x, "id", "id_str", "tweetId")
        post = str(g(x, "conversationId", "conversation_id", "inReplyToId", "inReplyToStatusId") or "")
        if iid and str(iid) in alvo:  # a própria publicação, não uma resposta
            return None
        autor = g(x, "author.userName", "author.username", "user.screen_name")
        linha = {"publicado_em": collect_redes.data_iso(g(x, "createdAt", "created_at")), "texto": g(x, "fullText", "text"),
                 "curtidas": collect_redes.inteiro(g(x, "likeCount", "favoriteCount")),
                 "respostas": collect_redes.inteiro(g(x, "replyCount"))}
    else:
        raise ValueError(rede_id)
    if not iid:
        return None
    item = next((a for a in alvo if a and a in post), post)
    texto = " ".join(str(linha["texto"] or "").split())
    if not texto:
        return None
    return {"rede": rede_id, "comentario_id": str(iid), "item_id": item, "autor": str(autor or ""), **linha, "texto": texto}


def apify_rede(rede_id: str, cfg: dict, publicacoes: list[dict], apify_cfg: dict, executar, gasto_antes: float):
    teto_etapa = float(apify_cfg["etapas"][ETAPA])
    sobra = round(teto_etapa - gasto_antes, 5)
    n = int(cfg["por_publicacao"])
    previsto = round(len(publicacoes) * n * float(cfg["preco_item"]), 5)
    if previsto > sobra:
        cabe = int(sobra * 0.9 / (n * float(cfg["preco_item"]))) if cfg["preco_item"] else 0
        publicacoes = publicacoes[:cabe]
        previsto = round(len(publicacoes) * n * float(cfg["preco_item"]), 5)
    if not publicacoes:
        return [], [], {"situacao": "⛔ o teto da etapa não cabe nenhuma publicação", "previsto_usd": 0}, 0.0
    autorizacao.verificar(apify_cfg, ETAPA, previsto, gasto_antes)
    teto_exec = round(min(previsto * 1.3 + 0.02, sobra), 4)
    run, itens = executar(cfg["ator"], entrada(rede_id, publicacoes, n), teto_exec)
    c = max(apify.custo(run), 0.0)
    alvo = {p["item_id"] for p in publicacoes}
    vistos, linhas = set(), []
    for x in itens:
        linha = normalizar(rede_id, x, alvo)
        if linha and linha["comentario_id"] not in vistos:
            vistos.add(linha["comentario_id"])
            linhas.append(linha)
    resumo = {"situacao": "ok" if linhas else "⛔ nenhum comentário devolvido", "run": run.get("id"), "status": run.get("status"),
              "publicacoes_pedidas": len(publicacoes), "por_publicacao": n, "previsto_usd": previsto, "teto_exec_usd": teto_exec,
              "itens": len(itens), "chaves": sorted(itens[0].keys())[:40] if itens else None}
    return linhas, itens, resumo, round(c, 5)


# ------------------------------------------------------------------------------------------------ gravação


def gravar(privado: pathlib.Path, rede_id: str, carimbo: str, linhas: list[dict], brutos, publicacoes, manifesto) -> None:
    tabela = privado / "terceiros" / "comentarios" / rede_id / f"comentarios_{carimbo}.csv"
    tabela.parent.mkdir(parents=True, exist_ok=True)
    with open(tabela, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(linhas)
    manifesto.arquivo(tabela, privado, privado=True)
    bruto = privado / "bruto" / "comentarios" / rede_id / f"{carimbo}.json"
    bruto.parent.mkdir(parents=True, exist_ok=True)
    bruto.write_text(json.dumps({"publicacoes": publicacoes, "itens": brutos}, ensure_ascii=False), encoding="utf-8")
    manifesto.arquivo(bruto, privado, privado=True)


def agregado(rede_id: str, linhas: list[dict], publicacoes: list[dict], resumo: dict) -> dict:
    por_pub: dict[str, int] = {}
    for l in linhas:
        por_pub[l["item_id"]] = por_pub.get(l["item_id"], 0) + 1
    meses: dict[str, int] = {}
    for l in linhas:
        if l["publicado_em"]:
            meses[l["publicado_em"][:7]] = meses.get(l["publicado_em"][:7], 0) + 1
    return {"rede": rede_id, "publicacoes_escolhidas": len(publicacoes),
            "comentarios_informados_nas_escolhidas": sum(p["comentarios"] or 0 for p in publicacoes) if publicacoes else None,
            "comentarios_lidos": len(linhas), "publicacoes_com_comentario_lido": len(por_pub),
            "autores_distintos": len({l["autor"] for l in linhas if l["autor"]}) or None,
            "por_mes": dict(sorted(meses.items())), "situacao": resumo.get("situacao")}


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Comentários das publicações com mais conversa.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--redes", nargs="*", default=["youtube", "tiktok", "instagram", "x"])
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    coleta = comum.config("coleta")
    apify_cfg, cfgs = coleta["apify"], configuracao(coleta)
    inicio, fim = (d.isoformat() for d in rede.periodo_lido())
    token = os.environ.get(apify_cfg["segredo"], "").strip()
    executar = lambda ator, ent, teto: apify.rodar(token, ator, ent, teto)  # noqa: E731
    destino = comum.RAIZ / "data" / "comentarios" / "resumo.json"
    resumo_publico = comum.carregar(destino) if destino.exists() else {"redes": {}}
    ok = 0
    for rede_id in opcoes.redes:
        cfg = cfgs[rede_id]
        publicacoes = escolher(privado, rede_id, int(cfg["publicacoes"]), inicio, fim)
        manifesto = rede.Manifesto(f"comentarios_{rede_id}", {
            "rede": rede_id, "como_escolhe": f"as {cfg['publicacoes']} publicações do período com mais comentários informados",
            "por_publicacao": cfg["por_publicacao"], "ator": cfg.get("ator"), "publicacoes": [p["item_id"] for p in publicacoes]},
            opcoes.run_id, etapa="gratis" if rede_id == "youtube" else ETAPA)
        carimbo = rede.carimbo(manifesto.dados["iniciado_em"])
        if not publicacoes:
            manifesto.bloqueio("nenhuma publicação do período com comentários informados no repositório privado")
            manifesto.gravar()
            continue
        try:
            if rede_id == "youtube":
                chave = os.environ.get("YOUTUBE_API_KEY", "")
                if not chave:
                    raise RuntimeError("YOUTUBE_API_KEY ausente")
                linhas, reg = youtube(chave, publicacoes, int(cfg["por_publicacao"]))
                brutos, resumo, gasto = [], {"situacao": "ok" if linhas else "⛔ nenhum comentário", **reg}, 0.0
                if reg["cota_esgotada"]:
                    manifesto.bloqueio("cota diária do YouTube esgotada antes do fim da lista")
            else:
                if not token:
                    raise RuntimeError(f"{apify_cfg['segredo']} ausente")
                linhas, brutos, resumo, gasto = apify_rede(rede_id, cfg, publicacoes, apify_cfg, executar,
                                                           autorizacao.gasto_da_etapa(ETAPA))
        except autorizacao.GastoNaoAutorizado as erro:
            manifesto.bloqueio(f"trava de gasto: {erro}")
            manifesto.gravar()
            print(f"BLOQUEADO {rede_id}: {erro}")
            continue
        except Exception as erro:
            manifesto.bloqueio(f"{type(erro).__name__}: {rede.sem_chave(str(erro))}")
            manifesto.gravar()
            print(f"ERRO {rede_id}: {type(erro).__name__}")
            continue
        gravar(privado, rede_id, carimbo, linhas, brutos, publicacoes, manifesto)
        resumo_publico["redes"][rede_id] = {**agregado(rede_id, linhas, publicacoes, resumo), "obtido_em": manifesto.dados["iniciado_em"],
                                            "run_id": opcoes.run_id}
        informados = sum(p["comentarios"] or 0 for p in publicacoes)
        manifesto.dados["consulta"].update({k: v for k, v in resumo.items() if k != "situacao"})
        manifesto.dados.update({
            "universo": {"valor": informados, "fonte": "soma dos comentários que a rede informa nas publicações escolhidas"},
            "lido": len(linhas),
            "amostra": {"n": len(linhas), "como": (f"até {cfg['por_publicacao']} comentários por publicação, nas "
                                                   f"{len(publicacoes)} publicações do período com mais comentários informados")},
            "parou_por": "limite", "custo_usd": gasto})
        print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {rede_id}, {len(linhas)} comentários de "
              f"{len(publicacoes)} publicações", flush=True)
        ok += 1
    resumo_publico["nota"] = ("Só contagens. Texto e autor dos comentários ficam no repositório privado; os textos entram no "
                              "corpus público anonimizados.")
    comum.gravar(destino, resumo_publico)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
