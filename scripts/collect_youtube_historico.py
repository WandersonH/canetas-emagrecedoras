"""Carga histórica do YouTube: busca de cada termo mês a mês, do início do período lido até o mês da coleta.

A busca comum devolve os vídeos mais recentes primeiro e, nos termos grandes, só alcança semanas antes da coleta.
Fatiar por mês faz cada mês ter a sua própria amostra e a sua própria estimativa de total.

Cota: cada busca custa 100 unidades; a chave tem 10.000 por dia. O coletor guarda no privado o que já fez
(historico/youtube_estado.json) e retoma de onde parou. Ao receber "quota exceeded", grava o progresso e termina.
Ordem: do mês mais recente para o mais antigo, todos os termos de cada mês, para que um resultado parcial já sirva.

Por termo e mês: 1 página de 50 vídeos (ordem por data), a estimativa do YouTube para aquele mês (pageInfo.totalResults)
e se a leitura parou no limite.

Público: data/youtube/historico.json, só agregados. Bruto e tabela de vídeos de terceiros: privado.

Uso:
    python scripts/collect_youtube_historico.py --privado /caminho --run-id 123 [--paginas 1]
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
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_youtube as cy  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402


class CotaEsgotada(Exception):
    pass


def meses(inicio: datetime.date, fim: datetime.date) -> list[tuple[str, datetime.date, datetime.date]]:
    """[(AAAA-MM, primeiro dia, último dia)], do mais recente para o mais antigo, cortados no período."""
    saida, atual = [], inicio.replace(day=1)
    while atual <= fim:
        proximo = (atual + datetime.timedelta(days=32)).replace(day=1)
        saida.append((atual.strftime("%Y-%m"), max(atual, inicio), min(proximo - datetime.timedelta(days=1), fim)))
        atual = proximo
    return list(reversed(saida))


def cota(erro: Exception) -> bool:
    if isinstance(erro, urllib.error.HTTPError) and erro.code == 403:
        try:
            return "quota" in erro.read().decode("utf-8", "replace").lower()
        except Exception:
            return True
    return False


def buscar_mes(chave, termo, de, ate, paginas, leitor=rede.pegar_json) -> dict:
    respostas, ids, token = [], [], None
    for _ in range(paginas):
        try:
            r = leitor(cy.url_busca(chave, termo, de, ate, token))
        except Exception as erro:
            if cota(erro):
                raise CotaEsgotada() from erro
            raise
        respostas.append(r)
        ids += [i["id"]["videoId"] for i in r.get("items", []) if (i.get("id") or {}).get("videoId")]
        token = r.get("nextPageToken")
        if not token:
            break
    return {"estimativa": (respostas[0].get("pageInfo") or {}).get("totalResults") if respostas else None,
            "ids": ids, "no_limite": bool(token), "bruto": respostas}


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Carga histórica do YouTube, mês a mês.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--run-id", default=None)
    leitor.add_argument("--paginas", type=int, default=1)
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    chave = os.environ.get("YOUTUBE_API_KEY", "")
    inicio, fim = rede.periodo_lido()
    termos = [t["termo"] for t in rede.termos_de_busca()]
    estado_arq = privado / "historico" / "youtube_estado.json"
    estado = comum.carregar(estado_arq) if estado_arq.exists() else {"feitos": {}}
    manifesto = rede.Manifesto("youtube_historico", {"termos": termos, "inicio": inicio.isoformat(), "fim": fim.isoformat(),
                                                     "paginas_por_mes": opcoes.paginas, "ordem": "date"}, opcoes.run_id)
    pasta = privado / "bruto" / "youtube_historico" / rede.carimbo(manifesto.dados["iniciado_em"])
    feitos_agora, esgotou = [], False
    if not chave:
        manifesto.bloqueio("YOUTUBE_API_KEY ausente")
        esgotou = True
    for mes, de, ate in ([] if esgotou else meses(inicio, fim)):
        for termo in termos:
            chave_estado = f"{termo}|{mes}"
            # o mês corrente é sempre refeito, porque ainda está em andamento
            if chave_estado in estado["feitos"] and mes != fim.strftime("%Y-%m"):
                continue
            try:
                r = buscar_mes(chave, termo, de, ate, opcoes.paginas)
            except CotaEsgotada:
                esgotou = True
                break
            except Exception as erro:
                manifesto.bloqueio(f"'{termo}' {mes}: {type(erro).__name__}: {erro}")
                continue
            pasta.mkdir(parents=True, exist_ok=True)
            arquivo = pasta / f"{len(feitos_agora):04d}.json"
            arquivo.write_text(json.dumps({"termo": termo, "mes": mes, "paginas": r.pop("bruto")}, ensure_ascii=False), encoding="utf-8")
            estado["feitos"][chave_estado] = {"estimativa": r["estimativa"], "ids": r["ids"], "no_limite": r["no_limite"],
                                              "arquivo": str(arquivo.relative_to(privado)), "run_id": opcoes.run_id}
            feitos_agora.append(chave_estado)
        if esgotou:
            break
    comum.gravar(estado_arq, estado)
    # detalhes dos vídeos novos (1 unidade por lote de 50)
    videos_arq = privado / "historico" / "youtube_videos.json"
    videos = comum.carregar(videos_arq) if videos_arq.exists() else {}
    faltam = [v for f in estado["feitos"].values() for v in f["ids"] if v not in videos]
    faltam = list(dict.fromkeys(faltam))
    if chave and faltam:
        try:
            for v in cy.detalhes(chave, faltam):
                videos[v["id"]] = v
        except Exception as erro:
            manifesto.bloqueio(f"detalhes: {type(erro).__name__}")
    comum.gravar(videos_arq, videos)
    tabela = privado / "terceiros" / "youtube" / "historico_videos.csv"
    tabela.parent.mkdir(parents=True, exist_ok=True)
    termos_do_video = collections.defaultdict(set)
    for k, f in estado["feitos"].items():
        for v in f["ids"]:
            termos_do_video[v].add(k.split("|")[0])
    with open(tabela, "w", encoding="utf-8", newline="") as arq:
        e = csv.writer(arq)
        e.writerow(["video_id", "termos", "publicado_em", "canal_id", "canal", "titulo", "descricao", "visualizacoes", "curtidas", "comentarios", "duracao"])
        for vid, ts in termos_do_video.items():
            v = videos.get(vid)
            if not v:
                continue
            s, st = v["snippet"], v.get("statistics") or {}
            e.writerow([vid, "|".join(sorted(ts)), s.get("publishedAt"), s.get("channelId"), s.get("channelTitle"), s.get("title"),
                        " ".join((s.get("description") or "").split())[:2000], st.get("viewCount"), st.get("likeCount"),
                        st.get("commentCount"), (v.get("contentDetails") or {}).get("duration")])
    # agregado público
    todos = meses(inicio, fim)
    por_termo = []
    for termo in termos:
        linhas = []
        for mes, _, _ in sorted(todos):
            f = estado["feitos"].get(f"{termo}|{mes}")
            linhas.append({"mes": mes, "feito": bool(f), "estimativa": f["estimativa"] if f else None,
                           "lidos": len(f["ids"]) if f else None, "no_limite": f["no_limite"] if f else None})
        por_termo.append({"termo": termo, "meses": linhas})
    total_pares = len(termos) * len(todos)
    feitos = sum(1 for k in estado["feitos"] if k.split("|")[1] in {m for m, _, _ in todos})
    publico = {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
               "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
               "progresso": {"feitos": feitos, "total": total_pares, "esgotou_cota_neste_run": esgotou},
               "videos_distintos": len(termos_do_video), "canais_distintos": len({v["snippet"].get("channelId") for v in videos.values()}) or None,
               "nota": "Estimativa = total que o YouTube informa para o termo naquele mês (aproximado). Lidos = até 50 vídeos por termo e mês.",
               "por_termo": por_termo}
    destino = comum.RAIZ / "data" / "youtube" / "historico.json"
    comum.gravar(destino, publico)
    manifesto.arquivo(destino, comum.RAIZ)
    lido = sum(len(f["ids"]) for f in estado["feitos"].values())
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "estimativa do YouTube por termo e mês em data/youtube/historico.json; os termos se sobrepõem"},
        "lido": lido, "amostra": {"n": len(termos_do_video), "como": "vídeos distintos, até 50 por termo e mês, ordem por data"},
        "parou_por": "data_inicial" if feitos == total_pares else "limite",
    })
    manifesto.dados["consulta"]["feitos_neste_run"] = len(feitos_agora)
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {feitos} de {total_pares} pares termo × mês, "
          f"{len(feitos_agora)} neste run, {len(termos_do_video)} vídeos distintos{' (cota esgotada)' if esgotou else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
