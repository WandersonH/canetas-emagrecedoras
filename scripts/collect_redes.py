"""TikTok, Instagram, X e Kwai pela Apify: publicações que a busca de cada rede devolve para os termos de consulta.

Pago. Antes de cada rede, scripts/autorizacao.py confere o teto da etapa somando os custos dos manifestos.
Cada execução vai com teto de cobrança próprio (maxTotalChargeUsd).

Etapas:
- teste: dois termos (coleta.json, termos_teste), poucos itens, para medir custo real e formato de cada ator;
- publicacoes: todos os termos de consulta, com o número de itens por termo de coleta.json, reduzido se não couber.

Universo: as buscas das redes não informam total de resultados (⛔).
Amostra: publicações distintas com data de publicação dentro do período lido.
Privacidade: tudo é de terceiros (nenhum perfil confirmado). Bruto e tabela com conta, texto e link vão só para o
privado. No público ficam só agregados: contagens por rede, termo e mês, soma de engajamento e contas distintas.

Uso:
    python scripts/collect_redes.py --etapa teste --privado /caminho --run-id 123 [--redes tiktok x]
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apify  # noqa: E402
import autorizacao  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

REDES = ("tiktok", "instagram", "x", "kwai")
CAMPOS = ["rede", "item_id", "conta", "publicado_em", "texto", "visualizacoes", "curtidas", "comentarios",
          "compartilhamentos", "url", "termos"]


def g(x: dict, *chaves):
    """Primeiro campo presente (aceita caminho com ponto)."""
    for chave in chaves:
        v = x
        for parte in chave.split("."):
            v = v.get(parte) if isinstance(v, dict) else None
        if v not in (None, ""):
            return v
    return None


def inteiro(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


def data_iso(v) -> str | None:
    if v in (None, ""):
        return None
    try:
        f = float(v)
        if f > 1e12:
            f /= 1000
        return datetime.datetime.fromtimestamp(f, datetime.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        s = str(v)
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            return s[:10]
        for formato in ("%a %b %d %H:%M:%S %z %Y",):
            try:
                return datetime.datetime.strptime(s, formato).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def hashtag(termo: str) -> str:
    import unicodedata
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", termo) if unicodedata.category(c) != "Mn")
    return "".join(c for c in sem_acento.lower() if c.isalnum())


def entrada(rede_id: str, termo: str, n: int, inicio: datetime.date) -> dict:
    if rede_id == "tiktok":
        return {"keywords": [termo], "maxItems": n}
    if rede_id == "instagram":
        return {"hashtags": [hashtag(termo)], "resultsType": "posts", "resultsLimit": n}
    if rede_id == "x":
        return {"searchTerms": [f'"{termo}" lang:pt since:{inicio.isoformat()} -filter:retweets'], "maxItems": n, "queryType": "Top"}
    if rede_id == "kwai":
        return {"searchTerms": [termo], "expandSearchWithHashtag": False, "maxItems": n, "postedAfter": inicio.isoformat()}
    raise ValueError(rede_id)


def normalizar(rede_id: str, x: dict) -> dict | None:
    """Item bruto → linha comum. None para perfil, erro ou item sem identificador."""
    if x.get("demo") or x.get("error") or x.get("noResults"):
        return None
    if rede_id == "x":
        iid, conta = g(x, "id", "id_str", "tweetId"), g(x, "author.userName", "author.username", "user.screen_name")
        linha = {"publicado_em": data_iso(g(x, "createdAt", "created_at")), "texto": g(x, "fullText", "text"),
                 "visualizacoes": inteiro(g(x, "viewCount", "views")), "curtidas": inteiro(g(x, "likeCount", "favoriteCount")),
                 "comentarios": inteiro(g(x, "replyCount")),
                 "compartilhamentos": (inteiro(g(x, "retweetCount")) or 0) + (inteiro(g(x, "quoteCount")) or 0),
                 "url": g(x, "url", "twitterUrl")}
    elif rede_id == "tiktok":
        iid = g(x, "id", "aweme_id", "video_id", "videoId")
        conta = g(x, "author.uniqueId", "authorMeta.name", "channel.username", "author.username")
        linha = {"publicado_em": data_iso(g(x, "createTimeISO", "createTime", "create_time", "uploadedAt", "timestamp")),
                 "texto": g(x, "desc", "text", "description", "title"),
                 "visualizacoes": inteiro(g(x, "playCount", "stats.playCount", "views")),
                 "curtidas": inteiro(g(x, "diggCount", "stats.diggCount", "likes")),
                 "comentarios": inteiro(g(x, "commentCount", "stats.commentCount", "comments")),
                 "compartilhamentos": inteiro(g(x, "shareCount", "stats.shareCount", "shares")),
                 "url": g(x, "webVideoUrl", "postPage", "url")}
    elif rede_id == "instagram":
        iid = g(x, "code", "shortCode", "shortcode", "id")
        conta = g(x, "owner.username", "ownerUsername", "user.username", "username")
        linha = {"publicado_em": data_iso(g(x, "createdAt", "timestamp", "takenAt", "taken_at")),
                 "texto": g(x, "caption.text", "caption", "text"),
                 "visualizacoes": inteiro(g(x, "video.playCount", "videoPlayCount", "playCount", "viewCount")),
                 "curtidas": inteiro(g(x, "likeCount", "likesCount")), "comentarios": inteiro(g(x, "commentCount", "commentsCount")),
                 "compartilhamentos": inteiro(g(x, "shareCount", "reshareCount")), "url": g(x, "url")}
    elif rede_id == "kwai":
        if str(g(x, "type", "recordType") or "video").lower() in ("profile", "user", "creator"):
            return None
        iid = g(x, "videoId", "video_id", "photoId", "id")
        conta = g(x, "authorHandle", "author.handle", "author.username", "username")
        linha = {"publicado_em": data_iso(g(x, "uploadTime", "createTime", "timestamp", "publishedAt", "postedAt")),
                 "texto": g(x, "caption", "description", "title"),
                 "visualizacoes": inteiro(g(x, "viewCount", "views", "playCount")), "curtidas": inteiro(g(x, "likeCount", "likes")),
                 "comentarios": inteiro(g(x, "commentCount", "comments")), "compartilhamentos": inteiro(g(x, "shareCount", "shares")),
                 "url": g(x, "url", "videoUrl", "shareUrl")}
    else:
        raise ValueError(rede_id)
    if not iid:
        return None
    linha["texto"] = " ".join(str(linha["texto"] or "").split())
    return {"rede": rede_id, "item_id": str(iid), "conta": str(conta or ""), **linha}


def agregar(rede_id: str, linhas: list[dict], por_termo: list[dict]) -> dict:
    """Só contagens e somas. Nenhuma conta, texto ou link."""
    por_mes = collections.Counter((l["publicado_em"] or "")[:7] for l in linhas if l["publicado_em"])
    def soma(campo):
        vals = [l[campo] for l in linhas if l[campo] is not None]
        return sum(vals) if vals else None
    return {"rede": rede_id, "publicacoes": len(linhas) if por_termo else None,
            "contas_distintas": len({l["conta"] for l in linhas if l["conta"]}) or None,
            "por_mes": dict(sorted(por_mes.items())), "visualizacoes_soma": soma("visualizacoes"),
            "curtidas_soma": soma("curtidas"), "comentarios_soma": soma("comentarios"),
            "por_termo": [{k: t[k] for k in ("termo", "itens", "lidos", "no_periodo", "no_limite", "mais_antigo", "erro")} for t in por_termo]}


def coletar_rede(rede_id: str, etapa: str, termos: list[str], cfg: dict, apify_cfg: dict, inicio, fim, executar,
                 gasto_antes: float) -> tuple[list[dict], list[dict], dict, float]:
    """Roda os termos de uma rede dentro do que sobra do teto da etapa. Devolve (linhas, brutos, resumo, custo)."""
    teto_etapa = float(apify_cfg["etapas"][etapa])
    sobra = round(teto_etapa - gasto_antes, 5)
    preco_item, preco_consulta = cfg["preco"]["item"], cfg["preco"].get("consulta", 0.0)
    n = cfg["itens_teste"] if etapa == "teste" else cfg["itens_por_termo"]
    previsto = len(termos) * (preco_consulta + preco_item * n)
    if previsto > sobra and etapa != "teste":  # reduz itens por termo para caber
        n = int((sobra * 0.9 / len(termos) - preco_consulta) / preco_item) if preco_item else 0
        previsto = len(termos) * (preco_consulta + preco_item * n)
    if n < 5:
        return [], [], {"situacao": "⛔ o teto da etapa não cabe nem 5 itens por termo", "itens_por_termo": n}, 0.0
    autorizacao.verificar(apify_cfg, etapa, round(previsto, 5), gasto_antes)
    linhas: dict[str, dict] = {}
    brutos, por_termo, gasto = [], [], 0.0
    for termo in termos:
        teto_exec = round(min(preco_consulta + preco_item * n * 1.3 + 0.01, sobra - gasto), 4)
        registro = {"termo": termo, "itens": 0, "lidos": 0, "no_periodo": 0, "no_limite": False, "mais_antigo": None,
                    "erro": None, "run": None, "custo_usd": 0.0}
        if teto_exec < 0.005:
            registro["erro"] = "teto da etapa esgotado"
            por_termo.append(registro)
            continue
        try:
            run, itens = executar(cfg["ator"], entrada(rede_id, termo, n, inicio), teto_exec)
            c = max(apify.custo(run), round(preco_consulta + preco_item * len(itens), 5))
            registro.update(run=run.get("id"), custo_usd=c, itens=len(itens), no_limite=len(itens) >= n,
                            chaves=sorted(itens[0].keys())[:40] if itens else None)
            gasto += c
        except Exception as erro:
            registro["erro"] = apify.erro_curto(erro)
            itens = []
        normais = [l for l in (normalizar(rede_id, x) for x in itens) if l]
        no_periodo = [l for l in normais if l["publicado_em"] and inicio.isoformat() <= l["publicado_em"] <= fim.isoformat()]
        registro.update(lidos=len(normais), no_periodo=len(no_periodo),
                        mais_antigo=min((l["publicado_em"] for l in no_periodo), default=None))
        for l in no_periodo:
            linha = linhas.setdefault(l["item_id"], {**l, "termos": []})
            if termo not in linha["termos"]:
                linha["termos"].append(termo)
        brutos += [{**x, "_termo": termo} for x in itens]
        por_termo.append(registro)
        print(f"{rede_id} '{termo}': {len(itens)} itens, {len(no_periodo)} no período{' · ' + registro['erro'] if registro['erro'] else ''}")
    resumo = {"situacao": "ok" if linhas else "⛔ nada no período", "itens_por_termo": n, "previsto_usd": round(previsto, 4),
              "por_termo": por_termo}
    return list(linhas.values()), brutos, resumo, round(gasto, 5)


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Busca por termo nas redes pagas.")
    leitor.add_argument("--etapa", choices=("teste", "publicacoes"), required=True)
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--run-id", default=None)
    leitor.add_argument("--redes", nargs="*", default=list(REDES))
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    coleta = comum.config("coleta")
    apify_cfg = coleta["apify"]
    token = os.environ.get(apify_cfg["segredo"], "").strip()
    inicio, fim = rede.periodo_lido()
    termos = coleta["termos_teste"] if opcoes.etapa == "teste" else [t["termo"] for t in rede.termos_de_busca()]
    executar = lambda ator, ent, teto: apify.rodar(token, ator, ent, teto)  # noqa: E731
    agregados, falhas = {}, 0
    for rede_id in opcoes.redes:
        cfg = coleta["pagas"][rede_id]
        manifesto = rede.Manifesto(rede_id, {"termos": termos, "ator": cfg["ator"], "busca": cfg["busca"],
                                             "inicio": inicio.isoformat(), "fim": fim.isoformat()}, opcoes.run_id, etapa=opcoes.etapa)
        if not token:
            manifesto.bloqueio(f"{apify_cfg['segredo']} ausente")
            manifesto.gravar()
            falhas += 1
            continue
        try:
            gasto_antes = autorizacao.gasto_da_etapa(opcoes.etapa)
            linhas, brutos, resumo, gasto = coletar_rede(rede_id, opcoes.etapa, termos, cfg, apify_cfg, inicio, fim, executar, gasto_antes)
        except autorizacao.GastoNaoAutorizado as erro:
            manifesto.bloqueio(f"trava de gasto: {erro}")
            manifesto.gravar()
            print(f"BLOQUEADO {rede_id}: {erro}")
            falhas += 1
            continue
        carimbo = rede.carimbo(manifesto.dados["iniciado_em"])
        bruto = privado / "bruto" / rede_id / f"{opcoes.etapa}_{carimbo}.json"
        bruto.parent.mkdir(parents=True, exist_ok=True)
        bruto.write_text(json.dumps(brutos, ensure_ascii=False), encoding="utf-8")
        manifesto.arquivo(bruto, privado, privado=True)
        tabela = privado / "terceiros" / rede_id / f"{opcoes.etapa}_{carimbo}.csv"
        tabela.parent.mkdir(parents=True, exist_ok=True)
        with open(tabela, "w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            escritor.writeheader()
            for l in linhas:
                escritor.writerow({**l, "termos": "|".join(l["termos"])})
        manifesto.arquivo(tabela, privado, privado=True)
        agregados[rede_id] = {**agregar(rede_id, linhas, resumo.get("por_termo") or []), "etapa": opcoes.etapa,
                              "itens_por_termo": resumo.get("itens_por_termo"), "obtido_em": manifesto.dados["iniciado_em"]}
        consultou = any(not t.get("erro") for t in resumo.get("por_termo") or [])
        for t in resumo.get("por_termo") or []:
            if t.get("erro"):
                manifesto.bloqueio(f"'{t['termo']}': {t['erro']}")
        manifesto.dados.update({
            "consulta": {**manifesto.dados["consulta"], "itens_por_termo": resumo.get("itens_por_termo"),
                         "previsto_usd": resumo.get("previsto_usd"), "por_termo": resumo.get("por_termo")},
            "universo": {"valor": None, "fonte": "A busca da rede não informa o total de resultados."},
            "lido": sum(t["lidos"] for t in resumo.get("por_termo") or []) if consultou else None,
            "amostra": {"n": len(linhas) if consultou else None,
                        "como": f"publicações distintas, com data no período lido, entre até {resumo.get('itens_por_termo')} itens por termo"},
            "parou_por": ("limite" if any(t["no_limite"] for t in resumo["por_termo"]) else "fim_dos_resultados") if consultou else None,
            "custo_usd": gasto,
        })
        print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {rede_id}, {len(linhas)} publicações no período")
        falhas += 0 if consultou else 1
    destino = comum.RAIZ / "data" / "redes" / f"{opcoes.etapa}.json"
    anterior = comum.carregar(destino) if destino.exists() else {"redes": {}}
    anterior["redes"].update(agregados)
    anterior.update({"nota": "Só agregados. Conta, texto e link de terceiros ficam no repositório privado.",
                     "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()}, "run_id": opcoes.run_id})
    comum.gravar(destino, anterior)
    return 1 if falhas == len(opcoes.redes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
