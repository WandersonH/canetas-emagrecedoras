"""Monta data/estado.json: o resumo das coletas que a página lê.

Entrada: os manifestos de data/manifestos/*.json. Cada coleta grava um manifesto com:
    coleta, frente, etapa, run_id, iniciado_em, terminado_em, consulta,
    universo {valor, fonte}, lido, amostra {n, como}, parou_por, custo_usd, arquivos [{caminho, sha256, linhas}]

Regras aplicadas aqui:
- frente sem manifesto fica com tudo null (a página mostra ⛔), nunca zero;
- universo que a plataforma não informa fica null;
- cobertura só é "completa" quando a leitura parou pela data inicial, e não pelo limite;
- custo nunca entra no estado: fica nos manifestos e não aparece na página.

Uso:
    python scripts/build_estado.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

PAROU_COMPLETO = "data_inicial"


def frentes(coleta: dict) -> list[dict]:
    """Lista as frentes de coleta na ordem da configuração, com nome e forma de acesso."""
    lista = []
    for chave, dados in (coleta.get("gratuitas") or {}).items():
        lista.append({"id": chave, "nome": dados["nome"], "via": dados["via"], "paga": False})
    for chave, dados in (coleta.get("pagas") or {}).items():
        lista.append({"id": chave, "nome": dados["nome"], "via": dados["via"], "paga": True})
    return lista


def cobertura(manifesto: dict) -> str:
    """'completa' só quando a leitura parou pela data inicial."""
    return "completa" if manifesto.get("parou_por") == PAROU_COMPLETO else "parcial"


def resumo_da_frente(frente: dict, manifestos: list[dict]) -> dict:
    """Resume os manifestos de uma frente. Sem manifesto, tudo fica null."""
    meus = [m for m in manifestos if m.get("frente") == frente["id"]]
    if not meus:
        return {**frente, "coletas": None, "universo": None, "universo_fonte": None, "lido": None,
                "amostra": None, "amostra_como": None, "cobertura": None, "ultima_coleta": None, "runs": []}
    meus.sort(key=lambda m: str(m.get("terminado_em") or ""))
    ultimo = meus[-1]
    universo = ultimo.get("universo") or {}
    amostra = ultimo.get("amostra") or {}
    return {
        **frente,
        "coletas": len(meus),
        "universo": universo.get("valor"),
        "universo_fonte": universo.get("fonte"),
        "lido": ultimo.get("lido"),
        "amostra": amostra.get("n"),
        "amostra_como": amostra.get("como"),
        "cobertura": cobertura(ultimo),
        "ultima_coleta": ultimo.get("terminado_em"),
        "runs": [str(m.get("run_id")) for m in meus if m.get("run_id")],
    }


def montar(coleta: dict, manifestos: list[dict]) -> dict:
    """Devolve o estado completo. Nenhum campo de custo passa por aqui."""
    return {
        "nota": "Gerado por scripts/build_estado.py a partir dos manifestos. Campo null é dado ausente.",
        "manifestos_lidos": len(manifestos) if manifestos else None,
        "frentes": [resumo_da_frente(frente, manifestos) for frente in frentes(coleta)],
    }


def ler_manifestos(pasta: pathlib.Path | None = None) -> list[dict]:
    pasta = pasta or comum.MANIFESTOS
    if not pasta.exists():
        return []
    return [comum.carregar(caminho) for caminho in sorted(pasta.glob("*.json"))]


def main() -> int:
    estado = montar(comum.config("coleta"), ler_manifestos())
    destino = comum.RAIZ / "data" / "estado.json"
    comum.gravar(destino, estado)
    com_dado = sum(1 for frente in estado["frentes"] if frente["coletas"])
    print(f"gravado {destino.relative_to(comum.RAIZ)}: {len(estado['frentes'])} frentes, {com_dado} com coleta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
