"""Entrada de CHANGELOG para commits feitos por workflow, no mesmo commit dos dados.

Cada entrada segue o formato do projeto: o que mudou, por quê, o que foi executado (com o ID do run),
o que ficou pendente e onde está a evidência. A entrada entra logo abaixo do cabeçalho, acima das demais.

Uso:
    python scripts/changelog_auto.py --titulo "..." --mudou "..." --porque "..." --executado "..." \
        --pendente "..." --evidencia "..." [--data 23/11/2026]
Cada opção pode se repetir; cada repetição vira um item.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

SECOES = [("mudou", "O que mudou"), ("porque", "Por quê"), ("executado", "O que foi executado de verdade"),
          ("pendente", "O que ficou pendente"), ("evidencia", "Onde está a evidência")]


def entrada(titulo: str, data: str, partes: dict[str, list[str]]) -> str:
    blocos = [f"## {data} · {titulo}"]
    for chave, rotulo in SECOES:
        itens = [item.strip() for item in partes.get(chave) or [] if item and item.strip()]
        if not itens:
            raise ValueError(f"a seção '{rotulo}' não pode ficar vazia")
        blocos.append(f"**{rotulo}**\n\n" + "\n".join(f"- {item}" for item in itens))
    return "\n\n".join(blocos) + "\n"


def inserir(texto_atual: str, nova: str) -> str:
    """Põe a entrada antes da primeira entrada existente (primeira linha que começa com '## ')."""
    linhas = texto_atual.splitlines(keepends=True)
    for indice, linha in enumerate(linhas):
        if linha.startswith("## "):
            return "".join(linhas[:indice]) + nova + "\n" + "".join(linhas[indice:])
    separador = "" if texto_atual.endswith("\n\n") or not texto_atual else ("\n" if texto_atual.endswith("\n") else "\n\n")
    return texto_atual + separador + nova


def main(argumentos: list[str] | None = None) -> int:
    leitor = argparse.ArgumentParser(description="Acrescenta uma entrada ao CHANGELOG.md.")
    leitor.add_argument("--titulo", required=True)
    leitor.add_argument("--data", default=None, help="dd/mm/aaaa; padrão: hoje em Brasília")
    for chave, _ in SECOES:
        leitor.add_argument(f"--{chave}", action="append", default=[])
    leitor.add_argument("--arquivo", default=str(comum.RAIZ / "CHANGELOG.md"))
    opcoes = leitor.parse_args(argumentos)
    data = opcoes.data or (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime("%d/%m/%Y")
    partes = {chave: getattr(opcoes, chave) for chave, _ in SECOES}
    caminho = pathlib.Path(opcoes.arquivo)
    atual = caminho.read_text(encoding="utf-8") if caminho.exists() else "# CHANGELOG\n\n"
    caminho.write_text(inserir(atual, entrada(opcoes.titulo, data, partes)), encoding="utf-8")
    print(f"entrada acrescentada em {caminho.name}: {opcoes.titulo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
