"""Imprensa: resultados do Google Notícias (RSS público, sem chave e sem custo) para cada termo de consulta, mês a mês.

Fonte: https://news.google.com/rss/search, Brasil e português, com os operadores after: e before: para cada mês do
período lido. A ordem é a do Google. O RSS devolve no máximo 100 itens por consulta: quando um mês chega a 100,
a leitura daquele mês parou no limite.

Universo: o Google não informa o total (⛔).
Saída pública: data/imprensa/resultados.json, com título, veículo, data e link de cada notícia e a contagem por termo
e mês. Notícia é publicação de veículo, não de pessoa comum.

Uso:
    python scripts/collect_imprensa.py --run-id 123
"""
from __future__ import annotations

import argparse
import collections
import datetime
import email.utils
import html
import pathlib
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402

URL = "https://news.google.com/rss/search"
LIMITE_RSS = 100
PAUSA = 1.0


def meses(inicio: datetime.date, fim: datetime.date) -> list[tuple[datetime.date, datetime.date]]:
    """Fatias de um mês: [início, primeiro dia do mês seguinte), cortadas no período lido."""
    fatias, atual = [], inicio
    while atual <= fim:
        proximo = (atual.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        fatias.append((atual, min(proximo, fim + datetime.timedelta(days=1))))
        atual = proximo
    return fatias


def url_rss(termo: str, de: datetime.date, ate: datetime.date) -> str:
    q = f'"{termo}" after:{de.isoformat()} before:{ate.isoformat()}'
    return f"{URL}?{urllib.parse.urlencode({'q': q, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'})}"


def ler_rss(conteudo: bytes) -> list[dict]:
    raiz = ET.fromstring(conteudo)
    itens = []
    for item in raiz.iter("item"):
        fonte = item.find("source")
        data = item.findtext("pubDate")
        try:
            data = email.utils.parsedate_to_datetime(data).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d") if data else None
        except (TypeError, ValueError):
            data = None
        titulo = html.unescape(item.findtext("title") or "")
        veiculo = fonte.text if fonte is not None else None
        if veiculo and titulo.endswith(f" - {veiculo}"):
            titulo = titulo[: -len(veiculo) - 3]
        itens.append({"titulo": titulo, "veiculo": veiculo,
                      "site": fonte.get("url") if fonte is not None else None,
                      "data": data, "link": item.findtext("link")})
    return itens


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Google Notícias por termo e mês.")
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    inicio, fim = rede.periodo_lido(gratuita=True)
    termos = rede.termos_de_busca()
    fatias = meses(inicio, fim)
    manifesto = rede.Manifesto("imprensa", {"termos": [t["termo"] for t in termos], "inicio": inicio.isoformat(),
                                            "fim": fim.isoformat(), "fatia": "mês", "limite_por_consulta": LIMITE_RSS,
                                            "fonte": URL, "regiao": "BR", "idioma": "pt-BR"}, opcoes.run_id)
    por_link: dict[str, dict] = {}
    contagem = collections.defaultdict(dict)
    lidos, consultas, no_limite = 0, 0, []
    for t in termos:
        for de, ate in fatias:
            mes = de.strftime("%Y-%m")
            try:
                itens = ler_rss(rede.pegar(url_rss(t["termo"], de, ate)))
            except Exception as erro:
                manifesto.bloqueio(f"'{t['termo']}' {mes}: {type(erro).__name__}: {erro}")
                continue
            finally:
                time.sleep(PAUSA)
            consultas += 1
            lidos += len(itens)
            contagem[t["termo"]][mes] = len(itens)
            if len(itens) >= LIMITE_RSS:
                no_limite.append(f"{t['termo']} {mes}")
            for item in itens:
                if not item["link"]:
                    continue
                linha = por_link.setdefault(item["link"], {**item, "termos": []})
                if t["termo"] not in linha["termos"]:
                    linha["termos"].append(t["termo"])
        print(f"{t['termo']}: {sum(contagem[t['termo']].values())} itens em {len(contagem[t['termo']])} meses")
    noticias = sorted(por_link.values(), key=lambda x: (x["data"] or "", x["link"]), reverse=True)
    destino = comum.RAIZ / "data" / "imprensa" / "resultados.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
                           "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
                           "consultas": consultas, "consultas_no_limite": no_limite,
                           "por_termo_e_mes": {k: dict(sorted(v.items())) for k, v in contagem.items()},
                           "noticias": noticias})
    manifesto.arquivo(destino, comum.RAIZ)
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "O Google Notícias não informa o total de resultados."},
        "lido": lidos if consultas else None,
        "amostra": {"n": len(noticias) if consultas else None,
                    "como": f"notícias distintas (link) do RSS, por termo e mês, até {LIMITE_RSS} por consulta"},
        "parou_por": ("limite" if no_limite else "fim_dos_resultados") if consultas else None,
    })
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {len(noticias)} notícias, {len(no_limite)} consultas no limite")
    return 0 if consultas else 1


if __name__ == "__main__":
    raise SystemExit(main())
