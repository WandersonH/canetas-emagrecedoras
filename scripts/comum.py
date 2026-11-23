"""Funções comuns: caminhos, leitura de JSON e a marca de dado ausente.

Dado ausente é AUSENTE (⛔), nunca zero. Quem escreve número na página lê de arquivo,
manifesto ou run identificável.
"""
from __future__ import annotations

import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "data" / "config"
MANIFESTOS = RAIZ / "data" / "manifestos"
AUSENTE = "⛔"


def carregar(caminho: pathlib.Path | str):
    """Lê um JSON em UTF-8."""
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def config(nome: str, raiz: pathlib.Path | None = None):
    """Lê data/config/<nome>.json."""
    base = (raiz or RAIZ) / "data" / "config"
    return carregar(base / f"{nome}.json")


def gravar(caminho: pathlib.Path | str, dado) -> None:
    """Grava JSON estável: UTF-8, indentado, com quebra de linha no fim."""
    caminho = pathlib.Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dado, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")


def ou_ausente(valor):
    """Devolve o valor, ou ⛔ quando ele não existe. Zero é valor e passa."""
    if valor is None or valor == "" or valor == [] or valor == {}:
        return AUSENTE
    return valor
