"""Totais que as próprias plataformas informam para os termos (universo informado).

Só existe número oficial para hashtag; para busca por frase, só o YouTube dá uma estimativa.
- Instagram: página da hashtag (apify~instagram-scraper, resultsType "details") → postsCount, de todos os tempos.
  Pago, na etapa de teste: cerca de US$ 0,0026 por hashtag, com trava de gasto e teto de US$ 0,10.
- TikTok: página pública da hashtag, lida com navegador sem login (grátis) → videoCount e viewCount, de todos os tempos.
- YouTube: estimativa por termo já gravada em data/youtube/agregado.json (pageInfo.totalResults).
- X e Kwai: não informam total (⛔).

Saída pública: data/universo/contagens.json.
Uso: python scripts/contagens_plataforma.py --run-id 123 [--sem-instagram] [--sem-tiktok]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import re
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apify  # noqa: E402
import autorizacao  # noqa: E402
import collect_redes  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

ATOR_INSTAGRAM = "apify~instagram-scraper"
PRECO_HASHTAG = 0.0026


def numero(v):
    return int(v) if str(v or "").isdigit() else None


def instagram(tags: list[str], executar) -> tuple[list[dict], dict]:
    entrada = {"directUrls": [f"https://www.instagram.com/explore/tags/{t}/" for t in tags], "resultsType": "details", "resultsLimit": 1}
    run, itens = executar(ATOR_INSTAGRAM, entrada, 0.10)
    por = {}
    for x in itens or []:
        nome = str(x.get("name") or x.get("hashtag") or "").lstrip("#").lower() or \
            re.sub(r".*/tags/([^/]+)/?.*", r"\1", str(x.get("url") or x.get("inputUrl") or "")).lower()
        por[nome] = x
    saida = [{"hashtag": t, "total_posts": numero((por.get(t) or {}).get("postsCount") or (por.get(t) or {}).get("mediaCount")),
              "fonte": "Instagram, página da hashtag (postsCount), todos os tempos"} for t in tags]
    return saida, run


async def _tiktok(tags: list[str]) -> list[dict]:
    from playwright.async_api import async_playwright
    saida = []
    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        pagina = await navegador.new_page(locale="pt-BR")
        for t in tags:
            reg = {"hashtag": t, "total_videos": None, "total_visualizacoes": None,
                   "fonte": "TikTok, página pública da hashtag (challengeInfo.stats), todos os tempos"}
            try:
                await pagina.goto(f"https://www.tiktok.com/tag/{urllib.parse.quote(t)}", wait_until="domcontentloaded", timeout=45000)
                await pagina.wait_for_timeout(2500)
                txt = await pagina.evaluate("() => (document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__')||{}).textContent || ''")
                dado = json.loads(txt) if txt else {}
                ch = ((dado.get("__DEFAULT_SCOPE__") or {}).get("webapp.challenge-detail") or {}).get("challengeInfo") or {}
                st = ch.get("statsV2") or ch.get("stats") or {}
                reg["total_videos"], reg["total_visualizacoes"] = numero(st.get("videoCount")), numero(st.get("viewCount"))
                if reg["total_videos"] is None:
                    reg["erro"] = "página sem dados da hashtag (inexistente ou bloqueio)"
            except Exception as erro:
                reg["erro"] = type(erro).__name__
            saida.append(reg)
        await navegador.close()
    return saida


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Totais informados pelas plataformas.")
    leitor.add_argument("--run-id", default=None)
    leitor.add_argument("--sem-instagram", action="store_true")
    leitor.add_argument("--sem-tiktok", action="store_true")
    opcoes = leitor.parse_args(argumentos)
    termos = [t["termo"] for t in rede.termos_de_busca()]
    tags = list(dict.fromkeys(collect_redes.hashtag(t) for t in termos))
    coleta = comum.config("coleta")
    destino = comum.RAIZ / "data" / "universo" / "contagens.json"
    saida = comum.carregar(destino) if destino.exists() else {}
    saida.update({"nota": "Totais de hashtag são de todos os tempos e só contam quem usou a hashtag. Busca por frase não tem total publicado, exceto a estimativa do YouTube.",
                  "termos": [{"termo": t, "hashtag": collect_redes.hashtag(t)} for t in termos],
                  "x": {"total": None, "fonte": "o X não informa total de publicações por termo"},
                  "kwai": {"total": None, "fonte": "o Kwai não informa total de publicações por termo"}})
    yt = comum.RAIZ / "data" / "youtube" / "agregado.json"
    if yt.exists():
        a = comum.carregar(yt)
        saida["youtube"] = {"obtido_em": a.get("obtido_em"), "run_id": a.get("run_id"),
                            "por_termo": [{"termo": t["termo"], "total_estimado": t["universo_estimado"]} for t in a["por_termo"]],
                            "fonte": "YouTube Data API, pageInfo.totalResults (estimativa arredondada) no período lido"}
    if not opcoes.sem_instagram:
        manifesto = rede.Manifesto("instagram_universo", {"hashtags": tags, "ator": ATOR_INSTAGRAM}, opcoes.run_id, etapa="teste")
        token = os.environ.get(coleta["apify"]["segredo"], "").strip()
        try:
            autorizacao.verificar(coleta["apify"], "teste", round(PRECO_HASHTAG * len(tags), 4), autorizacao.gasto_da_etapa("teste"))
            if not token:
                raise RuntimeError("token ausente")
            ig, run = instagram(tags, lambda a, e, c: apify.rodar(token, a, e, c))
            manifesto.dados["custo_usd"] = max(apify.custo(run), round(PRECO_HASHTAG * len(tags), 5))
            saida["instagram"] = {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id, "por_hashtag": ig}
            lidos = sum(1 for x in ig if x["total_posts"] is not None)
            manifesto.dados.update(lido=lidos, amostra={"n": lidos, "como": "hashtags com total informado"},
                                   universo={"valor": None, "fonte": "contagem de universo, não amostra"}, parou_por="fim_dos_resultados")
        except Exception as erro:
            manifesto.bloqueio(f"{type(erro).__name__}: {erro}")
        print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: universo do Instagram")
    if not opcoes.sem_tiktok:
        tt = asyncio.run(_tiktok(tags))
        saida["tiktok"] = {"obtido_em": rede.agora(), "run_id": opcoes.run_id, "por_hashtag": tt}
        print("tiktok:", [(x["hashtag"], x["total_videos"]) for x in tt])
    comum.gravar(destino, saida)
    print(f"gravado {destino.relative_to(comum.RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
