"""Checagens das agências brasileiras sobre as canetas emagrecedoras, pelo Google Notícias (RSS), sem custo.

A Fact Check Tools API trouxe poucas checagens em português. Aqui a busca vai ao Google Notícias restrita ao site
de cada agência (operador site:), no período lido (after: e before:), com dois grupos de termos: substâncias e
marcas ou nomes populares.

Universo: o Google Notícias não informa o total de resultados (⛔). O RSS devolve até 100 itens por consulta;
consulta que chega a 100 fica marcada como "no limite".
O estudo não dá veredito: mostra título, agência, data e link da própria checagem.

Saída pública: data/checagens/agencias.json.

Uso:
    python scripts/collect_checagens_agencias.py --run-id 123
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_imprensa as imprensa  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

# (nome, restrição da busca). A restrição vai inteira para a consulta.
AGENCIAS = [
    ("Agência Lupa", "site:lupa.uol.com.br"),
    ("Agência Lupa", "site:lupa.news"),
    ("Aos Fatos", "site:aosfatos.org"),
    ("Estadão Verifica", '"Estadão Verifica" site:estadao.com.br'),
    ("Fato ou Fake (g1)", '"Fato ou Fake" site:g1.globo.com'),
    ("AFP Checamos", "site:checamos.afp.com"),
    ("Projeto Comprova", "site:projetocomprova.com.br"),
    ("UOL Confere", '"UOL Confere" site:uol.com.br'),
    ("Boatos.org", "site:boatos.org"),
    ("E-farsas", "site:e-farsas.com"),
]
GRUPOS = {
    "substancias": ["semaglutida", "tirzepatida", "liraglutida", "retatrutida"],
    "marcas_e_nomes": ["Ozempic", "Wegovy", "Mounjaro", "Saxenda", "caneta emagrecedora", "canetas emagrecedoras"],
}


def consulta(restricao: str, termos: list[str], de: datetime.date, ate: datetime.date) -> str:
    ou = " OR ".join(f'"{t}"' if " " in t else t for t in termos)
    return f"({ou}) {restricao} after:{de.isoformat()} before:{ate.isoformat()}"


def url(q: str) -> str:
    return f"{imprensa.URL}?{urllib.parse.urlencode({'q': q, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'})}"


def coletar(inicio: datetime.date, fim: datetime.date, leitor=rede.pegar, pausa: float = imprensa.PAUSA):
    consultas, por_link = [], {}
    for agencia, restricao in AGENCIAS:
        for grupo, termos in GRUPOS.items():
            q = consulta(restricao, termos, inicio, fim + datetime.timedelta(days=1))
            registro = {"agencia": agencia, "restricao": restricao, "grupo": grupo, "consulta": q,
                        "lidos": None, "no_limite": None, "erro": None}
            try:
                itens = imprensa.ler_rss(leitor(url(q)))
            except Exception as erro:
                registro["erro"] = rede.sem_chave(f"{type(erro).__name__}: {erro}")[:200]
                consultas.append(registro)
                continue
            registro["lidos"] = len(itens)
            registro["no_limite"] = len(itens) >= imprensa.LIMITE_RSS
            consultas.append(registro)
            for item in itens:
                if not item.get("link") or not item.get("data") or item["data"] < inicio.isoformat():
                    continue
                linha = por_link.setdefault(item["link"], {**item, "agencia": agencia, "grupos": []})
                if grupo not in linha["grupos"]:
                    linha["grupos"].append(grupo)
            print(f"{agencia} · {grupo}: {len(itens)} itens", flush=True)
            time.sleep(pausa)
    return consultas, sorted(por_link.values(), key=lambda x: (x["data"], x["link"]), reverse=True)


def main(argumentos=None, leitor=rede.pegar, raiz: pathlib.Path | None = None) -> int:
    opcoes = argparse.ArgumentParser(description="Checagens das agências brasileiras.")
    opcoes.add_argument("--run-id", default=None)
    opcoes = opcoes.parse_args(argumentos)
    raiz = raiz or comum.RAIZ
    inicio, fim = rede.periodo_lido(raiz)
    manifesto = rede.Manifesto("checagens_agencias", {"fonte": imprensa.URL, "agencias": AGENCIAS, "grupos": GRUPOS,
                                                      "inicio": inicio.isoformat(), "fim": fim.isoformat()},
                               opcoes.run_id)
    consultas, checagens = coletar(inicio, fim, leitor)
    destino = raiz / "data" / "checagens" / "agencias.json"
    por_agencia: dict[str, int] = {}
    for c in checagens:
        por_agencia[c["agencia"]] = por_agencia.get(c["agencia"], 0) + 1
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
                           "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
                           "nota": "Títulos e links das próprias agências, pelo Google Notícias. O estudo não dá veredito.",
                           "consultas": consultas, "por_agencia": por_agencia, "checagens": checagens})
    manifesto.arquivo(destino, raiz)
    respondidas = [c for c in consultas if c["lidos"] is not None]
    for c in consultas:
        if c["erro"]:
            manifesto.bloqueio(f"{c['agencia']} · {c['grupo']}: {c['erro']}")
    manifesto.dados.update({
        "universo": {"valor": None, "fonte": "O Google Notícias não informa o total de resultados."},
        "lido": sum(c["lidos"] for c in respondidas) if respondidas else None,
        "amostra": {"n": len(checagens) if respondidas else None,
                    "como": "links distintos das agências, com data no período lido"},
        "parou_por": ("limite" if any(c["no_limite"] for c in respondidas) else "fim_dos_resultados") if respondidas else None,
    })
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: {len(checagens)} checagens de agências brasileiras")
    return 0 if respondidas else 1


if __name__ == "__main__":
    raise SystemExit(main())
