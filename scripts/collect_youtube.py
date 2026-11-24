"""YouTube: vídeos que a busca do YouTube devolve para cada termo de consulta, no período lido.

Fonte: YouTube Data API (search.list e videos.list). Sem custo em dólar; gasta cota diária da chave
(100 unidades por página de busca, 1 por lote de 50 vídeos).

Como a amostra é tirada: para cada termo, busca no Brasil e em português, ordenada por data (mais recente primeiro),
entre o início do período lido e a data da coleta, até MAX_PAGINAS páginas de 50.

Universo: o YouTube informa, por termo, uma estimativa de resultados (pageInfo.totalResults), que a própria
documentação diz ser aproximada. Ela fica por termo no agregado. Como os termos se sobrepõem, não há soma que
sirva de universo da frente: no manifesto o universo fica ⛔.

Privacidade: os vídeos são de terceiros (ainda não há perfil confirmado). Título, canal e identificador vão só
para o repositório privado. No público ficam só agregados (contagens por termo e por mês, soma de visualizações).

Uso:
    python scripts/collect_youtube.py --privado /caminho/do/privado --run-id 123
Reconstrução sem nova consulta à API, a partir do bruto já guardado no privado:
    python scripts/collect_youtube.py --privado /caminho/do/privado --run-id 123 --do-bruto bruto/youtube/<carimbo>
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
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402

API = "https://www.googleapis.com/youtube/v3"
MAX_PAGINAS = 5
POR_PAGINA = 50


def url_busca(chave: str, termo: str, inicio: datetime.date, fim: datetime.date, pagina: str | None) -> str:
    parametros = {"part": "snippet", "type": "video", "q": termo, "regionCode": "BR", "relevanceLanguage": "pt",
                  "order": "date", "maxResults": POR_PAGINA, "key": chave,
                  "publishedAfter": f"{inicio.isoformat()}T00:00:00Z",
                  "publishedBefore": f"{(fim + datetime.timedelta(days=1)).isoformat()}T00:00:00Z"}
    if pagina:
        parametros["pageToken"] = pagina
    return f"{API}/search?{urllib.parse.urlencode(parametros)}"


def buscar_termo(chave: str, termo: str, inicio, fim, leitor=rede.pegar_json) -> dict:
    paginas, ids, token, universo, parou = [], [], None, None, None
    for numero in range(MAX_PAGINAS):
        resposta = leitor(url_busca(chave, termo, inicio, fim, token))
        paginas.append(resposta)
        if numero == 0:
            universo = (resposta.get("pageInfo") or {}).get("totalResults")
        ids += [item["id"]["videoId"] for item in resposta.get("items", []) if (item.get("id") or {}).get("videoId")]
        token = resposta.get("nextPageToken")
        if not token:
            parou = "fim_dos_resultados"
            break
    else:
        parou = "limite"
    return {"termo": termo, "universo_estimado": universo, "lido": len(ids), "ids": ids, "paginas": len(paginas),
            "parou_por": parou, "bruto": paginas}


def detalhes(chave: str, ids: list[str], leitor=rede.pegar_json) -> list[dict]:
    itens = []
    for i in range(0, len(ids), 50):
        lote = ",".join(ids[i:i + 50])
        q = urllib.parse.urlencode({"part": "snippet,statistics,contentDetails", "id": lote, "key": chave})
        itens += leitor(f"{API}/videos?{q}").get("items", [])
    return itens


def inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def agregar(buscas: list[dict], videos: list[dict], inicio, fim) -> dict:
    """Só contagens: nenhum título, canal ou identificador."""
    por_id = {v["id"]: v for v in videos}
    termos_do_video = collections.defaultdict(set)
    for busca in buscas:
        for vid in busca["ids"]:
            termos_do_video[vid].add(busca["termo"])
    por_mes = collections.Counter()
    canais = set()
    views = comentarios = 0
    com_estatistica = 0
    for vid in termos_do_video:
        v = por_id.get(vid)
        if not v:
            continue
        canais.add(v["snippet"].get("channelId"))
        por_mes[v["snippet"]["publishedAt"][:7]] += 1
        est = v.get("statistics") or {}
        if est.get("viewCount") is not None:
            com_estatistica += 1
            views += inteiro(est.get("viewCount")) or 0
            comentarios += inteiro(est.get("commentCount")) or 0
    termo_mes = collections.defaultdict(collections.Counter)
    for busca in buscas:
        for vid in set(busca["ids"]):
            v = por_id.get(vid)
            if v:
                termo_mes[busca["termo"]][v["snippet"]["publishedAt"][:7]] += 1
    return {
        "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
        "por_termo": [{"termo": b["termo"], "universo_estimado": b["universo_estimado"], "lido": b["lido"],
                       "distintos": len(set(b["ids"])), "paginas": b["paginas"], "parou_por": b["parou_por"],
                       "por_mes": dict(sorted(termo_mes[b["termo"]].items()))} for b in buscas],
        "videos_distintos": len(termos_do_video),
        "videos_com_detalhe": sum(1 for vid in termos_do_video if vid in por_id),
        "canais_distintos": len(canais) if canais else None,
        "por_mes": dict(sorted(por_mes.items())),
        "visualizacoes_soma": views if com_estatistica else None,
        "comentarios_soma": comentarios if com_estatistica else None,
        "videos_em_mais_de_um_termo": sum(1 for t in termos_do_video.values() if len(t) > 1),
    }


def ler_bruto(pasta: pathlib.Path) -> tuple[list[dict], list[dict]]:
    """Refaz as buscas e os detalhes a partir dos arquivos guardados, sem chamar a API."""
    buscas = []
    for caminho in sorted(pasta.glob("busca_*.json")):
        dado = json.loads(caminho.read_text(encoding="utf-8"))
        paginas = dado["paginas"]
        ids = [i["id"]["videoId"] for p in paginas for i in p.get("items", []) if (i.get("id") or {}).get("videoId")]
        ultimo_token = paginas[-1].get("nextPageToken") if paginas else None
        buscas.append({"termo": dado["termo"], "universo_estimado": (paginas[0].get("pageInfo") or {}).get("totalResults") if paginas else None,
                       "lido": len(ids), "ids": ids, "paginas": len(paginas),
                       "parou_por": "limite" if ultimo_token and len(paginas) >= MAX_PAGINAS else "fim_dos_resultados"})
    videos = json.loads((pasta / "videos.json").read_text(encoding="utf-8"))
    return buscas, videos


def reconstruir(privado: pathlib.Path, pasta: pathlib.Path, run_id: str | None) -> int:
    buscas, videos = ler_bruto(pasta)
    carimbo = pasta.name  # AAAAMMDDTHHMMSSZ do início da coleta original
    iniciado = f"{carimbo[0:4]}-{carimbo[4:6]}-{carimbo[6:8]}T{carimbo[9:11]}:{carimbo[11:13]}:{carimbo[13:15]}Z"
    inicio, fim = rede.periodo_lido(hoje=datetime.date.fromisoformat(iniciado[:10]), gratuita=True)
    manifesto = rede.Manifesto("youtube", {"termos": [b["termo"] for b in buscas], "inicio": inicio.isoformat(),
                                           "fim": fim.isoformat(), "ordem": "date", "regiao": "BR", "idioma": "pt",
                                           "max_paginas_por_termo": MAX_PAGINAS, "por_pagina": POR_PAGINA,
                                           "reconstrucao": f"Refeito do bruto guardado no privado ({pasta.relative_to(privado)}), sem nova consulta à API; a gravação pública do run original falhou."},
                               run_id)
    manifesto.dados["iniciado_em"] = iniciado
    for caminho in sorted(pasta.glob("*.json")):
        manifesto.arquivo(caminho, privado, privado=True)
    for tabela in sorted((privado / "terceiros" / "youtube").glob(f"videos_{carimbo}.csv")):
        manifesto.arquivo(tabela, privado, privado=True)
    return publicar(manifesto, buscas, videos, inicio, fim, run_id, iniciado)


def publicar(manifesto, buscas, videos, inicio, fim, run_id, obtido_em) -> int:
    agregado = agregar(buscas, videos, inicio, fim)
    agregado.update({"obtido_em": obtido_em, "run_id": run_id})
    destino = comum.RAIZ / "data" / "youtube" / "agregado.json"
    comum.gravar(destino, agregado)
    manifesto.arquivo(destino, comum.RAIZ)
    lido = sum(b["lido"] for b in buscas) if buscas else None
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "O YouTube informa só uma estimativa por termo (pageInfo.totalResults), registrada em data/youtube/agregado.json; os termos se sobrepõem e a soma não é universo."},
        "lido": lido,
        "amostra": {"n": agregado["videos_distintos"] if buscas else None,
                    "como": f"vídeos distintos da busca por data, até {MAX_PAGINAS} páginas de {POR_PAGINA} por termo"},
        "parou_por": "limite" if any(b["parou_por"] == "limite" for b in buscas) else ("fim_dos_resultados" if buscas else None),
    })
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {agregado['videos_distintos']} vídeos distintos")
    return 0 if buscas else 1


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Coleta de vídeos do YouTube por termo.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--run-id", default=None)
    leitor.add_argument("--do-bruto", default=None, help="pasta do bruto no privado; não consulta a API")
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    if opcoes.do_bruto:
        return reconstruir(privado, privado / opcoes.do_bruto, opcoes.run_id)
    chave = os.environ.get("YOUTUBE_API_KEY", "")
    inicio, fim = rede.periodo_lido(gratuita=True)
    termos = rede.termos_de_busca()
    manifesto = rede.Manifesto("youtube", {"termos": [t["termo"] for t in termos], "inicio": inicio.isoformat(),
                                           "fim": fim.isoformat(), "ordem": "date", "regiao": "BR", "idioma": "pt",
                                           "max_paginas_por_termo": MAX_PAGINAS, "por_pagina": POR_PAGINA},
                               opcoes.run_id)
    if not chave:
        manifesto.bloqueio("YOUTUBE_API_KEY ausente")
        manifesto.gravar()
        print("BLOQUEADO: YOUTUBE_API_KEY ausente")
        return 1
    pasta = privado / "bruto" / "youtube" / rede.carimbo(manifesto.dados["iniciado_em"])
    pasta.mkdir(parents=True, exist_ok=True)
    buscas = []
    for t in termos:
        try:
            busca = buscar_termo(chave, t["termo"], inicio, fim)
        except Exception as erro:  # cota esgotada, chave recusada, rede
            manifesto.bloqueio(f"busca '{t['termo']}': {type(erro).__name__}: {erro}")
            continue
        caminho = pasta / f"busca_{len(buscas):02d}.json"
        caminho.write_text(json.dumps({"termo": t["termo"], "paginas": busca.pop("bruto")}, ensure_ascii=False), encoding="utf-8")
        manifesto.arquivo(caminho, privado, privado=True)
        buscas.append(busca)
        print(f"{t['termo']}: estimativa {busca['universo_estimado']}, lidos {busca['lido']}, {busca['parou_por']}")
    ids = list(dict.fromkeys(vid for b in buscas for vid in b["ids"]))
    videos = []
    try:
        videos = detalhes(chave, ids)
    except Exception as erro:
        manifesto.bloqueio(f"detalhes: {type(erro).__name__}: {erro}")
    caminho = pasta / "videos.json"
    caminho.write_text(json.dumps(videos, ensure_ascii=False), encoding="utf-8")
    manifesto.arquivo(caminho, privado, privado=True)
    tabela = privado / "terceiros" / "youtube" / f"videos_{rede.carimbo(manifesto.dados['iniciado_em'])}.csv"
    tabela.parent.mkdir(parents=True, exist_ok=True)
    termos_do_video = collections.defaultdict(list)
    for b in buscas:
        for vid in b["ids"]:
            termos_do_video[vid].append(b["termo"])
    with open(tabela, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["video_id", "termos", "publicado_em", "canal_id", "canal", "titulo", "visualizacoes",
                           "curtidas", "comentarios", "duracao"])
        for v in videos:
            s, e = v["snippet"], v.get("statistics") or {}
            escritor.writerow([v["id"], "|".join(dict.fromkeys(termos_do_video[v["id"]])), s.get("publishedAt"),
                               s.get("channelId"), s.get("channelTitle"), s.get("title"), e.get("viewCount"),
                               e.get("likeCount"), e.get("commentCount"), (v.get("contentDetails") or {}).get("duration")])
    manifesto.arquivo(tabela, privado, privado=True)
    return publicar(manifesto, buscas, videos, inicio, fim, opcoes.run_id, manifesto.dados["iniciado_em"])


if __name__ == "__main__":
    raise SystemExit(main())
