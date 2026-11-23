"""Sondagem das fontes de dados públicos: o que existe em cada endereço, sem baixar os arquivos.

Para cada fonte, grava o código HTTP, o tamanho e o SHA-256 da página lida e a lista de arquivos que ela
oferece (nome, endereço, data e tamanho quando a página informa). Para as pastas do SNGPC, resume quais
meses estão publicados. Nenhum número do estudo sai daqui: a sondagem só diz o que a fonte oferece.

Saída: data/fontes/sondagem.json

Uso:
    python scripts/sondar_fontes.py --run-id 123
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402

AGENTE = "Mozilla/5.0 (compatible; pesquisa-canetas-emagrecedoras; +https://github.com/WandersonH/canetas-emagrecedoras)"
EXTENSOES = (".csv", ".zip", ".xls", ".xlsx", ".pdf", ".json", ".txt", ".gz")
FONTES = [
    {"id": "anvisa_dados", "nome": "Anvisa, portal de dados abertos (pasta principal)",
     "url": "https://dados.anvisa.gov.br/dados/", "tipo": "indice", "frente": "anvisa_vigimed"},
    {"id": "sngpc_industrializados", "nome": "Anvisa, SNGPC, vendas de industrializados",
     "url": "https://dados.anvisa.gov.br/dados/SNGPC/Industrializados/", "tipo": "indice", "frente": "anvisa_sngpc"},
    {"id": "sngpc_manipulados", "nome": "Anvisa, SNGPC, vendas de manipulados",
     "url": "https://dados.anvisa.gov.br/dados/SNGPC/Manipulados/", "tipo": "indice", "frente": "anvisa_sngpc"},
    {"id": "cmed_precos", "nome": "CMED, página das listas de preços",
     "url": "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos", "tipo": "pagina", "frente": "cmed_precos"},
]

_ANCORA = re.compile(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<a\s|\Z)', re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_DATA = re.compile(r"(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?|\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2})")
_TAMANHO = re.compile(r"(?<![\d:-])(\d+(?:\.\d+)?[KMGT]?)\s*$")
_MES = re.compile(r"(20\d{2})(0[1-9]|1[0-2])(?!\d)")


def _limpar(trecho: str) -> str:
    return " ".join(html.unescape(_TAG.sub(" ", trecho)).split())


def ler_indice(pagina: str, base: str) -> list[dict]:
    """Arquivos e pastas de uma listagem de diretório. Ignora a pasta de cima e os links de ordenação."""
    itens = []
    for href, texto, resto in _ANCORA.findall(pagina):
        href = html.unescape(href)
        url = urllib.parse.urljoin(base, href)
        if href.startswith(("?", "#")) or not url.startswith(base) or url.rstrip("/") == base.rstrip("/"):
            continue  # ordenação, âncora, pasta de cima ou link para fora da pasta
        nome = _limpar(texto)
        if not nome or nome.lower() in ("parent directory", "diretório pai", "..", "name", "nome"):
            continue
        cauda = _limpar(resto)
        data = _DATA.search(cauda)
        tamanho = _TAMANHO.search(cauda)
        itens.append({
            "nome": nome,
            "url": url,
            "pasta": href.endswith("/"),
            "data": data.group(1) if data else None,
            "tamanho": tamanho.group(1) if tamanho and not href.endswith("/") else None,
        })
    return itens


def ler_pagina(pagina: str, base: str) -> list[dict]:
    """Links para arquivos (planilha, CSV, ZIP, PDF) numa página comum."""
    itens, vistos = [], set()
    for href, texto, _ in _ANCORA.findall(pagina):
        url = urllib.parse.urljoin(base, html.unescape(href))
        caminho = urllib.parse.urlparse(url).path.lower()
        if not caminho.endswith(EXTENSOES) and "/@@download" not in caminho:
            continue
        if url in vistos:
            continue
        vistos.add(url)
        itens.append({"nome": _limpar(texto) or caminho.rsplit("/", 1)[-1], "url": url, "pasta": False,
                      "data": None, "tamanho": None})
    return itens


def meses_publicados(itens: list[dict]) -> dict:
    """Meses (AAAAMM) que aparecem no nome dos arquivos. Sem mês reconhecível, tudo null."""
    meses = sorted({f"{a}{m}" for item in itens if not item["pasta"] for a, m in _MES.findall(item["nome"])})
    if not meses:
        return {"quantidade": None, "primeiro": None, "ultimo": None, "lista": []}
    return {"quantidade": len(meses), "primeiro": meses[0], "ultimo": meses[-1], "lista": meses}


def baixar(url: str, tempo: int = 60, tentativas: int = 3) -> dict:
    """Lê uma página, com novas tentativas. Nunca levanta exceção: o erro vai para o resultado."""
    resultado = {}
    for tentativa in range(tentativas):
        resultado = _baixar_uma_vez(url, tempo)
        if resultado["http"] == 200 or (resultado["http"] and resultado["http"] < 500 and resultado["http"] != 429):
            return resultado
        time.sleep(5 * (tentativa + 1))
    return resultado


def _baixar_uma_vez(url: str, tempo: int) -> dict:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html,*/*",
                                                  "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
            corpo = resposta.read()
            return {"http": resposta.status, "tipo": resposta.headers.get("Content-Type"), "corpo": corpo, "erro": None}
    except urllib.error.HTTPError as erro:
        return {"http": erro.code, "tipo": None, "corpo": b"", "erro": f"HTTP {erro.code}"}
    except Exception as erro:  # rede, tempo esgotado, certificado
        return {"http": None, "tipo": None, "corpo": b"", "erro": f"{type(erro).__name__}: {erro}"[:300]}


def sondar(fonte: dict, leitor=baixar, pasta_paginas: pathlib.Path | None = None) -> dict:
    resposta = leitor(fonte["url"])
    corpo = resposta["corpo"]
    texto = corpo.decode("utf-8", errors="replace")
    itens = []
    if resposta["http"] == 200 and corpo:
        itens = ler_indice(texto, fonte["url"]) if fonte["tipo"] == "indice" else ler_pagina(texto, fonte["url"])
    if corpo and pasta_paginas is not None:
        pasta_paginas.mkdir(parents=True, exist_ok=True)
        (pasta_paginas / f"{fonte['id']}.html").write_bytes(corpo)
    resultado = {
        "id": fonte["id"], "nome": fonte["nome"], "url": fonte["url"], "frente": fonte["frente"],
        "http": resposta["http"], "tipo_conteudo": resposta["tipo"], "erro": resposta["erro"],
        "bytes": len(corpo) if corpo else None,
        "sha256": hashlib.sha256(corpo).hexdigest() if corpo else None,
        "arquivos": len([i for i in itens if not i["pasta"]]) if resposta["http"] == 200 else None,
        "pastas": len([i for i in itens if i["pasta"]]) if resposta["http"] == 200 else None,
        "itens": itens,
    }
    if fonte["id"].startswith("sngpc_"):
        resultado["meses"] = meses_publicados(itens)
    return resultado


def montar(run_id: str | None, leitor=baixar, agora: datetime.datetime | None = None,
           pasta_paginas: pathlib.Path | None = None) -> dict:
    agora = agora or datetime.datetime.now(datetime.timezone.utc)
    return {
        "nota": "Gerado por scripts/sondar_fontes.py. Diz o que cada fonte oferece; não traz número do estudo.",
        "obtido_em": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "paginas_lidas": "data/fontes/paginas/ (cópia de cada página lida, para conferência)" if pasta_paginas else None,
        "fontes": [sondar(fonte, leitor, pasta_paginas) for fonte in FONTES],
    }


def resumo(sondagem: dict) -> list[str]:
    linhas = []
    for fonte in sondagem["fontes"]:
        if fonte["http"] != 200:
            linhas.append(f"{fonte['id']}: sem acesso ({fonte['erro']})")
            continue
        linha = f"{fonte['id']}: HTTP 200, {fonte['arquivos']} arquivos, {fonte['pastas']} pastas"
        meses = fonte.get("meses")
        if meses and meses["quantidade"]:
            linha += f", meses {meses['primeiro']} a {meses['ultimo']} ({meses['quantidade']})"
        linhas.append(linha)
    return linhas


def main(argumentos: list[str] | None = None) -> int:
    leitor_args = argparse.ArgumentParser(description="Sonda as fontes de dados públicos.")
    leitor_args.add_argument("--run-id", default=None)
    opcoes = leitor_args.parse_args(argumentos)
    sondagem = montar(opcoes.run_id, pasta_paginas=comum.RAIZ / "data" / "fontes" / "paginas")
    destino = comum.RAIZ / "data" / "fontes" / "sondagem.json"
    comum.gravar(destino, sondagem)
    for linha in resumo(sondagem):
        print(linha)
    print(f"gravado {destino.relative_to(comum.RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
