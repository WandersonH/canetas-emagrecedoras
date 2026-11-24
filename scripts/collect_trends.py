"""Google Trends (Brasil): interesse de busca pelos termos do estudo no período lido.

Lê os grupos de data/config/trends.json e grava, para cada grupo:
- a série no tempo (Brasil);
- o recorte por UF;
- as consultas e assuntos relacionados, nos grupos indicados.

Cuidados, registrados também no manifesto:
- O Trends não dá volume. Os valores vão de 0 a 100 e são relativos dentro de cada consulta: só compare termos do
  mesmo grupo e período.
- Cada consulta é uma amostra; repetir dá números um pouco diferentes. Cada coleta fica em pasta própria, sem
  sobrescrever.
- Não há API oficial aberta. O coletor usa os mesmos endereços da página do Trends; limite do Google (HTTP 429) é
  registrado como bloqueio.

Universo: não se aplica (índice relativo, sem total): ⛔.
Saída pública: data/trends/<carimbo>/ e data/trends/ultimo.json.

Uso:
    python scripts/collect_trends.py --run-id 123
"""
from __future__ import annotations

import argparse
import csv
import http.cookiejar
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402

BASE = "https://trends.google.com/trends"
IDIOMA, FUSO = "pt-BR", "180"


def sem_prefixo(texto: str):
    """As respostas do Trends começam com um prefixo de proteção, como )]}',"""
    return json.loads(texto[texto.index("{"):])


class Trends:
    def __init__(self, geo: str, pausa: float = 5.0):
        self.geo, self.pausa = geo, pausa
        self.abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self._get(f"{BASE}/?geo={geo}&hl={IDIOMA}", cru=True)

    def _get(self, url: str, cru: bool = False):
        corpo = rede.pegar(url, opener=self.abridor, pausa=self.pausa * 2,
                           cabecalhos={"Accept-Language": "pt-BR,pt;q=0.9"}).decode("utf-8")
        time.sleep(self.pausa)
        return corpo if cru else sem_prefixo(corpo)

    def explorar(self, termos: list[str], periodo: str) -> dict:
        pedido = {"comparisonItem": [{"keyword": t, "geo": self.geo, "time": periodo} for t in termos],
                  "category": 0, "property": ""}
        q = urllib.parse.urlencode({"hl": IDIOMA, "tz": FUSO, "req": json.dumps(pedido, ensure_ascii=False)})
        return {w["id"]: w for w in self._get(f"{BASE}/api/explore?{q}")["widgets"]}

    def widget(self, tipo: str, w: dict):
        q = urllib.parse.urlencode({"hl": IDIOMA, "tz": FUSO, "req": json.dumps(w["request"], ensure_ascii=False),
                                    "token": w["token"]})
        return self._get(f"{BASE}/api/widgetdata/{tipo}?{q}")


def gravar_serie(dado: dict, termos: list[str], caminho: pathlib.Path) -> int:
    linhas = dado["default"]["timelineData"]
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        e = csv.writer(arquivo, delimiter=";", lineterminator="\n")
        e.writerow(["inicio_utc", "rotulo"] + termos + ["parcial"])
        for linha in linhas:
            ts = time.strftime("%Y-%m-%d", time.gmtime(int(linha["time"])))
            e.writerow([ts, linha.get("formattedTime", "")] + linha["value"] + [int(bool(linha.get("isPartial")))])
    return len(linhas)


def gravar_uf(dado: dict, termos: list[str], caminho: pathlib.Path) -> int:
    linhas = dado["default"]["geoMapData"]
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        e = csv.writer(arquivo, delimiter=";", lineterminator="\n")
        e.writerow(["uf", "nome"] + termos)
        for linha in linhas:
            e.writerow([linha.get("geoCode"), linha.get("geoName")] + linha["value"])
    return len(linhas)


def gravar_relacionados(blocos: list[tuple[str, str, dict]], caminho: pathlib.Path) -> int:
    n = 0
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        e = csv.writer(arquivo, delimiter=";", lineterminator="\n")
        e.writerow(["termo", "tipo", "lista", "posicao", "texto", "valor", "valor_formatado"])
        for termo, tipo, dado in blocos:
            for nome, bloco in zip(("principais", "em_alta"), (dado.get("default") or {}).get("rankedList") or []):
                for posicao, k in enumerate(bloco.get("rankedKeyword") or [], 1):
                    texto = k.get("query") or (k.get("topic") or {}).get("title", "")
                    e.writerow([termo, tipo, nome, posicao, texto, k.get("value"), k.get("formattedValue")])
                    n += 1
    return n


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Google Trends dos termos do estudo.")
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    cfg = comum.config("trends")
    inicio, fim = rede.periodo_lido(gratuita=True)
    periodo = f"{inicio.isoformat()} {fim.isoformat()}"
    manifesto = rede.Manifesto("trends", {"grupos": cfg["grupos"], "periodo": periodo, "geo": cfg["geo"],
                                          "aviso": "Índice de 0 a 100 relativo dentro de cada grupo; não é volume."},
                               opcoes.run_id)
    pasta = comum.RAIZ / "data" / "trends" / rede.carimbo(manifesto.dados["iniciado_em"])
    pasta.mkdir(parents=True, exist_ok=True)
    resultado = {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id, "periodo": periodo,
                 "pasta": str(pasta.relative_to(comum.RAIZ)), "grupos": []}
    try:
        t = Trends(cfg["geo"], cfg.get("pausa_segundos", 5))
    except Exception as erro:
        t = None
        manifesto.bloqueio(f"sessão do Trends: {type(erro).__name__}: {erro}")
    pontos = 0
    for g in cfg["grupos"] if t else []:
        registro = {"nome": g["nome"], "termos": g["termos"], "serie": None, "uf": None, "relacionados": None}
        try:
            ws = t.explorar(g["termos"], periodo)
            serie = pasta / f"{g['nome']}__serie.csv"
            registro["pontos"] = gravar_serie(t.widget("multiline", ws["TIMESERIES"]), g["termos"], serie)
            registro["serie"] = serie.name
            manifesto.arquivo(serie, comum.RAIZ)
            pontos += registro["pontos"]
            geo = next((w for k, w in ws.items() if k.startswith("GEO_MAP")), None)
            if geo:
                uf = pasta / f"{g['nome']}__uf.csv"
                registro["ufs"] = gravar_uf(t.widget("comparedgeo", geo), g["termos"], uf)
                registro["uf"] = uf.name
                manifesto.arquivo(uf, comum.RAIZ)
            if g["nome"] in cfg.get("relacionados", []):
                blocos = []
                for k, w in sorted(ws.items()):
                    tipo = "consultas" if k.startswith("RELATED_QUERIES") else "assuntos" if k.startswith("RELATED_TOPICS") else None
                    if tipo:
                        i = int(k.rsplit("_", 1)[1]) if k.rsplit("_", 1)[-1].isdigit() else 0
                        blocos.append((g["termos"][i] if i < len(g["termos"]) else str(i), tipo, t.widget("relatedsearches", w)))
                rel = pasta / f"{g['nome']}__relacionados.csv"
                registro["linhas_relacionadas"] = gravar_relacionados(blocos, rel)
                registro["relacionados"] = rel.name
                manifesto.arquivo(rel, comum.RAIZ)
            registro["situacao"] = "ok"
        except Exception as erro:
            registro["situacao"] = f"erro: {type(erro).__name__}: {erro}"[:300]
            manifesto.bloqueio(f"grupo {g['nome']}: {type(erro).__name__}: {erro}")
        resultado["grupos"].append(registro)
        print(f"{g['nome']}: {registro['situacao']}")
    comum.gravar(pasta / "resumo.json", resultado)
    comum.gravar(comum.RAIZ / "data" / "trends" / "ultimo.json", resultado)
    ok = [g for g in resultado["grupos"] if g.get("situacao") == "ok"]
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "O Google Trends dá índice relativo de 0 a 100, sem total de buscas."},
        "lido": pontos if ok else None,
        "amostra": {"n": len(ok) if ok else None, "como": "grupos de termos com série semanal no Brasil (índice 0-100)"},
        "parou_por": "data_inicial" if ok and len(ok) == len(cfg["grupos"]) else ("bloqueio" if ok else None),
    })
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {len(ok)} de {len(cfg['grupos'])} grupos")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
