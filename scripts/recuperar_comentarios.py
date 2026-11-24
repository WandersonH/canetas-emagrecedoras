"""Refaz no repositório privado os arquivos de uma coleta de comentários já paga, a partir do conjunto de dados
que a própria execução da Apify guardou. Não roda ator nenhum e não gera custo.

Para cada manifesto: lê a execução (consulta.run), baixa os itens do conjunto de dados dela, normaliza como o
coletor normalizou e grava a tabela no mesmo caminho que o manifesto lista em arquivos_privados. Confere o SHA-256
com o do manifesto e imprime se bateu. O manifesto não é alterado.

Uso:
    python scripts/recuperar_comentarios.py --privado DIR data/manifestos/comentarios_x_....json [...]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apify  # noqa: E402
import collect_comentarios as cc  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402


def normalizar_itens(rede_id: str, itens: list[dict], alvo: set[str]) -> list[dict]:
    vistos, linhas = set(), []
    for x in itens:
        linha = cc.normalizar(rede_id, x, alvo)
        if linha and linha["comentario_id"] not in vistos:
            vistos.add(linha["comentario_id"])
            linhas.append(linha)
    return linhas


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Recupera no privado comentários de coletas já pagas.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("manifestos", nargs="+")
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    coleta = comum.config("coleta")
    token = os.environ.get(coleta["apify"]["segredo"], "").strip()
    if not token:
        print("BLOQUEADO: token da Apify ausente")
        return 1
    inicio, fim = (d.isoformat() for d in rede.periodo_lido())
    cfgs, falhas = cc.configuracao(coleta), 0
    for caminho in opcoes.manifestos:
        m = comum.carregar(pathlib.Path(caminho))
        rede_id, run_id = m["consulta"]["rede"], m["consulta"].get("run")
        if not run_id:
            print(f"ERRO {caminho}: manifesto sem execução da Apify")
            falhas += 1
            continue
        execucao = apify.api("GET", f"/actor-runs/{run_id}", token)["data"]
        itens = apify.baixar_itens(token, execucao["defaultDatasetId"])
        linhas = normalizar_itens(rede_id, itens, set(m["consulta"]["publicacoes"]))
        tabela = next(a for a in m["arquivos_privados"] if a["caminho"].endswith(".csv"))
        destino = privado / tabela["caminho"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=cc.CAMPOS)
            escritor.writeheader()
            escritor.writerows(linhas)
        bate = hashlib.sha256(destino.read_bytes()).hexdigest() == tabela["sha256"]
        bruto = next((a for a in m["arquivos_privados"] if a["caminho"].endswith(".json")), None)
        if bruto:
            publicacoes = cc.escolher(privado, rede_id, int(cfgs[rede_id]["publicacoes"]), inicio, fim)
            caminho_bruto = privado / bruto["caminho"]
            caminho_bruto.parent.mkdir(parents=True, exist_ok=True)
            caminho_bruto.write_text(json.dumps({"publicacoes": publicacoes, "itens": itens}, ensure_ascii=False), encoding="utf-8")
        print(f"recuperado {tabela['caminho']}: {rede_id}, {len(linhas)} comentários da execução {run_id}; "
              f"SHA-256 {'igual ao do manifesto' if bate else 'DIFERENTE do manifesto'}", flush=True)
        falhas += 0 if bate else 1
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
