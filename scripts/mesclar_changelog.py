"""Junta dois CHANGELOGs durante um rebase: mantém o do ramo remoto inteiro e põe no topo a entrada mais recente
do commit que está sendo reaplicado, se ela ainda não estiver lá. Nenhuma entrada é apagada.

Uso: python scripts/mesclar_changelog.py REMOTO MEU > CHANGELOG.md
"""
from __future__ import annotations

import pathlib
import sys


def primeira_entrada(texto: str) -> str | None:
    partes = texto.split("\n## ")
    if len(partes) < 2:
        return None
    resto = partes[1]
    return "## " + resto.split("\n## ")[0].rstrip() + "\n"


def mesclar(remoto: str, meu: str) -> str:
    entrada = primeira_entrada(meu)
    if not entrada or entrada.strip() in remoto:
        return remoto
    i = remoto.find("\n## ")
    if i < 0:
        return remoto.rstrip() + "\n\n" + entrada
    return remoto[: i + 1] + entrada + "\n" + remoto[i + 1:]


if __name__ == "__main__":
    remoto, meu = (pathlib.Path(p).read_text(encoding="utf-8") for p in sys.argv[1:3])
    sys.stdout.write(mesclar(remoto, meu))
