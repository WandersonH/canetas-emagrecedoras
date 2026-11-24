"""Proposições da Câmara dos Deputados sobre as canetas emagrecedoras (arquivos anuais de dados abertos, sem custo).

Fonte: https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-<ano>.csv, um arquivo por ano do
período lido. Cada arquivo é lido inteiro; ficam as proposições cuja ementa ou indexação cita substância, marca,
nome popular ou "GLP-1". (A busca por palavra-chave da API v2 recusou a consulta com HTTP 400 no run 45313922869.)

Universo: proposições do arquivo do ano (linhas lidas). Amostra: as que citam os termos.
Saída pública: data/dados_publicos/camara.json (proposições são documentos públicos do Legislativo).

Uso:
    python scripts/collect_camara.py --run-id 123
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_anvisa  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

URL = "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{ano}.csv"
EXTRAS = ["GLP-1", "caneta emagrecedora", "canetas emagrecedoras", "caneta para emagrecer", "canetas para emagrecer"]


def chaves(raiz: pathlib.Path | None = None) -> dict[str, str]:
    saida = collect_anvisa.chaves(raiz)
    for termo in EXTRAS:
        saida[collect_anvisa.normal(termo)] = termo.lower()
    return saida


def ler_ano(ano: int, pat: re.Pattern, abrir=collect_anvisa.abrir_remoto):
    with abrir(URL.format(ano=ano), tempo=300) as texto:
        return collect_anvisa.filtrar(texto, lambda maiuscula, _crua: pat.search(collect_anvisa.normal(maiuscula)) is not None)


def main(argumentos=None, abrir=collect_anvisa.abrir_remoto, raiz: pathlib.Path | None = None) -> int:
    opcoes = argparse.ArgumentParser(description="Proposições da Câmara sobre o tema.")
    opcoes.add_argument("--run-id", default=None)
    opcoes = opcoes.parse_args(argumentos)
    raiz = raiz or comum.RAIZ
    inicio, fim = rede.periodo_lido(raiz, gratuita=True)
    chaves_ = chaves(raiz)
    pat = collect_anvisa.padrao(chaves_)
    anos = list(range(inicio.year, fim.year + 1))
    manifesto = rede.Manifesto("dados_publicos", {"subfrente": "camara", "fonte": URL, "anos": anos,
                                                  "filtro": "ementa ou indexação que cita substância, marca, nome popular ou GLP-1"},
                               opcoes.run_id)
    arquivos, proposicoes, total = [], [], 0
    for ano in anos:
        try:
            cab, linhas, n, _ = ler_ano(ano, pat, abrir)
        except Exception as erro:
            manifesto.bloqueio(f"{ano}: {type(erro).__name__}: {erro}")
            arquivos.append({"ano": ano, "url": URL.format(ano=ano), "linhas_no_arquivo": None, "erro": str(erro)[:200]})
            continue
        total += n
        arquivos.append({"ano": ano, "url": URL.format(ano=ano), "linhas_no_arquivo": n, "linhas_que_citam": len(linhas),
                         "colunas": cab})
        col = {nome: collect_anvisa.coluna(cab, nome) for nome in ("SIGLATIPO", "NUMERO", "ANO", "EMENTA", "KEYWORDS",
                                                                  "DATAAPRESENTACAO", "URI")}
        col["ID"] = collect_anvisa._ou(collect_anvisa.coluna(cab, "ID", evitar=("TIPO", "ORGAO", "SITUACAO", "AUTOR")), 0)
        pega = lambda l, k: (l[col[k]].strip() if col.get(k) is not None and col[k] < len(l) else None)  # noqa: E731
        for l in linhas:
            data = (pega(l, "DATAAPRESENTACAO") or "")[:10]
            if data and not (inicio.isoformat() <= data <= fim.isoformat()):
                continue
            ident = pega(l, "ID")
            proposicoes.append({"id": ident, "tipo": pega(l, "SIGLATIPO"), "numero": pega(l, "NUMERO"), "ano": pega(l, "ANO"),
                                "apresentada_em": data or None, "ementa": pega(l, "EMENTA"),
                                "termos": collect_anvisa.substancias_da_linha([pega(l, "EMENTA") or "", pega(l, "KEYWORDS") or ""], chaves_, pat),
                                "link": f"https://www.camara.leg.br/propostas-legislativas/{ident}" if ident else None})
        print(f"camara {ano}: {n} proposições no arquivo, {len(linhas)} citam os termos", flush=True)
    por_tipo: dict[str, int] = {}
    for p in proposicoes:
        por_tipo[p["tipo"] or "não informado"] = por_tipo.get(p["tipo"] or "não informado", 0) + 1
    destino = raiz / "data" / "dados_publicos" / "camara.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id,
                           "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
                           "nota": "Proposições apresentadas no período cuja ementa ou indexação cita os termos.",
                           "arquivos": arquivos, "por_tipo": por_tipo,
                           "proposicoes": sorted(proposicoes, key=lambda p: p["apresentada_em"] or "", reverse=True)})
    manifesto.arquivo(destino, raiz)
    leu = any(a.get("linhas_no_arquivo") is not None for a in arquivos)
    manifesto.dados.update({
        "universo": {"valor": total if leu else None, "fonte": "proposições dos arquivos anuais da Câmara, contadas na leitura"},
        "lido": total if leu else None,
        "amostra": {"n": len(proposicoes) if leu else None, "como": "proposições do período que citam os termos"},
        "parou_por": "arquivo_inteiro" if leu else None})
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: camara, {len(proposicoes)} proposições")
    return 0 if leu else 1


if __name__ == "__main__":
    raise SystemExit(main())
