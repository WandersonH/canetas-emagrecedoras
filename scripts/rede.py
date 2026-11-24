"""Rede e manifesto, comuns a todos os coletores.

- `pegar` faz GET com identificação do projeto, tenta de novo em 429 e 5xx e nunca desliga a verificação de certificado.
- `Manifesto` grava o registro de cada coleta no formato que scripts/build_estado.py lê:
  frente, etapa, run_id, iniciado_em, terminado_em, consulta, universo {valor, fonte}, lido, amostra {n, como},
  parou_por, custo_usd, arquivos [{caminho, sha256, bytes, linhas}], bloqueios.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

AGENTE = "Mozilla/5.0 (compatible; pesquisa-canetas-emagrecedoras/1.0; +https://github.com/WandersonH/canetas-emagrecedoras)"


def agora() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def carimbo(iso: str) -> str:
    """'2026-11-23T20:30:00Z' -> '20261123T203000Z', para nome de pasta."""
    return iso.replace("-", "").replace(":", "")


def pegar(url: str, tentativas: int = 4, pausa: float = 3.0, tempo: int = 60, cabecalhos: dict | None = None,
          opener=None) -> bytes:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, **(cabecalhos or {})})
    espera = pausa
    for tentativa in range(tentativas):
        try:
            abrir = opener.open if opener else urllib.request.urlopen
            with abrir(pedido, timeout=tempo) as resposta:
                return resposta.read()
        except urllib.error.HTTPError as erro:
            if erro.code not in (429, 500, 502, 503, 504) or tentativa == tentativas - 1:
                raise
        except urllib.error.URLError:
            if tentativa == tentativas - 1:
                raise
        time.sleep(espera)
        espera *= 2
    raise RuntimeError("inalcançável")


def pegar_json(url: str, **kw):
    return json.loads(pegar(url, **kw))


def sem_chave(texto: str) -> str:
    """Tira de uma mensagem de erro qualquer valor de chave que esteja no ambiente."""
    for nome in ("YOUTUBE_API_KEY", "FACTCHECK_API_KEY", "APIFY_TOKEN_CANETAS", "ODI_INTERNO_TOKEN"):
        valor = os.environ.get(nome)
        if valor:
            texto = texto.replace(valor, "***")
    return texto


def ficha(caminho: pathlib.Path, raiz: pathlib.Path) -> dict:
    dado = caminho.read_bytes()
    linhas = dado.count(b"\n") if caminho.suffix in (".csv", ".txt") else None
    return {"caminho": str(caminho.relative_to(raiz)), "sha256": hashlib.sha256(dado).hexdigest(),
            "bytes": len(dado), "linhas": linhas}


class Manifesto:
    def __init__(self, frente: str, consulta: dict, run_id: str | None, etapa: str = "gratis"):
        self.dados = {"frente": frente, "etapa": etapa, "run_id": run_id, "iniciado_em": agora(), "terminado_em": None,
                      "consulta": consulta, "universo": {"valor": None, "fonte": None}, "lido": None,
                      "amostra": {"n": None, "como": None}, "parou_por": None, "custo_usd": 0,
                      "arquivos": [], "arquivos_privados": [], "bloqueios": []}

    def bloqueio(self, texto: str) -> None:
        self.dados["bloqueios"].append(sem_chave(texto)[:400])

    def arquivo(self, caminho: pathlib.Path, raiz: pathlib.Path, privado: bool = False) -> None:
        self.dados["arquivos_privados" if privado else "arquivos"].append(ficha(caminho, raiz))

    def gravar(self, raiz: pathlib.Path | None = None) -> pathlib.Path:
        raiz = raiz or comum.RAIZ
        self.dados["terminado_em"] = agora()
        destino = raiz / "data" / "manifestos" / f"{self.dados['frente']}_{carimbo(self.dados['iniciado_em'])}.json"
        comum.gravar(destino, self.dados)
        return destino


def termos_de_busca(raiz: pathlib.Path | None = None) -> list[dict]:
    """Termos marcados como consulta (busca: true), com a família de cada um."""
    familias = comum.config("termos", raiz)["familias"]
    return [{"termo": item["termo"], "familia": chave} for chave, familia in familias.items()
            for item in familia["itens"] if item.get("busca")]


def periodo_lido(raiz: pathlib.Path | None = None, hoje: datetime.date | None = None,
                 gratuita: bool = False) -> tuple[datetime.date, datetime.date]:
    """Período lido do projeto, em datas. Fim ausente é a data da coleta.

    gratuita=True usa janelas.periodo_lido_gratuitas (coletas sem custo), quando existe."""
    janelas = comum.config("projeto", raiz)["janelas"]
    janela = janelas.get("periodo_lido_gratuitas") if gratuita and janelas.get("periodo_lido_gratuitas") else janelas["periodo_lido"]
    inicio = datetime.datetime.strptime(janela["inicio"], "%d/%m/%Y").date()
    fim = datetime.datetime.strptime(janela["fim"], "%d/%m/%Y").date() if janela.get("fim") else (
        hoje or datetime.datetime.now(datetime.timezone.utc).date())
    return inicio, fim
