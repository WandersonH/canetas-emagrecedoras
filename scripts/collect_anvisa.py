"""Dados abertos da Anvisa sobre as substâncias das canetas: registro, preços (CMED), farmacovigilância (VigiMed)
e vendas em farmácias (SNGPC, industrializados e manipulados). Sem custo.

Fonte: https://dados.anvisa.gov.br/dados/ (arquivos CSV). Cada arquivo é lido inteiro, em fluxo, e só as linhas
que citam uma das substâncias ou marcas de data/config/termos.json são guardadas.

Universo: linhas do arquivo, contadas na própria leitura (o arquivo inteiro é o universo da fonte).
Lido: as mesmas linhas. Amostra: linhas que citam substância ou marca. parou_por = "arquivo_inteiro".

Privacidade:
- registro e preços são dados de empresas e produtos: as linhas filtradas vão ao público;
- VigiMed e SNGPC têm idade, sexo, peso e município de pacientes: as linhas filtradas ficam só no repositório
  privado; no público entram contagens agregadas, e contagem menor que 5 aparece como "<5".

Uso:
    python scripts/collect_anvisa.py --frentes registro cmed vigimed sngpc --privado DIR --run-id 123
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import io
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comum  # noqa: E402
import rede  # noqa: E402
import sondar_fontes  # noqa: E402

BASE = "https://dados.anvisa.gov.br/dados/"
ARQUIVOS = {
    "registro": ["DADOS_ABERTOS_MEDICAMENTOS.csv"],
    "cmed": ["TA_PRECO_MEDICAMENTO.csv", "TA_PRECOS_MEDICAMENTOS.csv"],
    "vigimed": ["VigiMed_Medicamentos.csv", "VigiMed_Notificacoes.csv", "VigiMed_Reacoes.csv"],
}
SNGPC = {"industrializados": BASE + "SNGPC/Industrializados/", "manipulados": BASE + "SNGPC/Manipulados/"}
MINIMO_PUBLICO = 5
TOPO = 25


def normal(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().upper().strip()


def chaves(raiz: pathlib.Path | None = None) -> dict[str, str]:
    """Forma normalizada -> substância. Marca aponta para a própria marca (a substância vem da coluna do arquivo)."""
    familias = comum.config("termos", raiz)["familias"]
    saida = {normal(i["termo"]): i["termo"].lower() for i in familias["substancias"]["itens"]}
    saida["RETATRUTIDA"] = "retatrutida"
    for item in familias["marcas"]["itens"]:  # marca conta pela substância quando o arquivo de termos a informa
        saida[normal(item["termo"])] = (item.get("substancia") or item["termo"]).lower() if item.get("substancia") else item["termo"]
    return saida


def padrao(chaves_: dict[str, str]) -> re.Pattern:
    return re.compile(r"\b(" + "|".join(sorted(map(re.escape, chaves_), key=len, reverse=True)) + r")\b")


def separador(cabecalho: str) -> str:
    return ";" if cabecalho.count(";") >= cabecalho.count(",") else ","


def codificacao(amostra: bytes) -> str:
    try:
        amostra.decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError as erro:
        # só o fim cortado no meio de um caractere conta como UTF-8
        return "utf-8-sig" if erro.reason == "unexpected end of data" else "latin-1"


def abrir_remoto(url: str, tempo: int = 180, tentativas: int = 3):
    """Texto do arquivo em fluxo, com a codificação deduzida do começo."""
    for tentativa in range(tentativas):
        try:
            resposta = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": rede.AGENTE}), timeout=tempo)
            bruto = io.BufferedReader(resposta, 1 << 20)
            return io.TextIOWrapper(bruto, encoding=codificacao(bruto.peek(1 << 16)), errors="replace", newline="")
        except Exception:
            if tentativa == tentativas - 1:
                raise
            time.sleep(10 * (tentativa + 1))


def filtrar(linhas, casar) -> tuple[list[str], list[list[str]], int, str]:
    """Lê cabeçalho e linhas; devolve (cabeçalho, linhas que casam, total de linhas de dados, separador).

    `casar(linha_maiuscula, linha_crua)` decide se a linha fica. A linha só é dividida em campos se ficar."""
    iterador = iter(linhas)
    cabecalho_cru = next(iterador, "")
    sep = separador(cabecalho_cru)
    cabecalho = [c.strip().strip('"').lstrip("﻿") for c in next(csv.reader([cabecalho_cru], delimiter=sep))]
    ficam, total = [], 0
    for linha in iterador:
        if not linha.strip():
            continue
        total += 1
        if casar(linha.upper(), linha):
            ficam.append(next(csv.reader([linha], delimiter=sep)))
    return cabecalho, ficam, total, sep


def coluna(cabecalho: list[str], *pedacos: str, evitar: tuple[str, ...] = ()) -> int | None:
    """Índice da primeira coluna cujo nome normalizado contém todos os pedaços."""
    for i, nome in enumerate(cabecalho):
        n = normal(nome)
        if all(p in n for p in pedacos) and not any(e in n for e in evitar):
            return i
    return None


def _ou(*indices):
    """Primeiro índice achado (0 é um índice válido)."""
    return next((i for i in indices if i is not None), None)


def substancias_da_linha(linha: list[str], chaves_: dict[str, str], pat: re.Pattern) -> list[str]:
    achadas = []
    for campo in linha:
        for m in pat.finditer(normal(campo)):
            valor = chaves_[m.group(1)]
            if valor not in achadas:
                achadas.append(valor)
    return achadas


def contar(valores) -> list[dict]:
    """Contagem decrescente; abaixo do mínimo vira '<5'."""
    c = collections.Counter(v if v not in (None, "") else "não informado" for v in valores)
    return [{"valor": k, "n": n if n >= MINIMO_PUBLICO else f"<{MINIMO_PUBLICO}"} for k, n in c.most_common()]


def gravar_csv(destino: pathlib.Path, cabecalho: list[str], linhas: list[list[str]]) -> None:
    """CSV em UTF-8; com final .gz, comprimido de forma reproduzível (sem data no cabeçalho do gzip)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.suffix == ".gz":
        with destino.open("wb") as bruto, gzip.GzipFile(fileobj=bruto, mode="wb", mtime=0) as comprimido, \
                io.TextIOWrapper(comprimido, encoding="utf-8", newline="") as saida:
            escritor = csv.writer(saida)
            escritor.writerow(cabecalho)
            escritor.writerows(linhas)
        return
    with destino.open("w", encoding="utf-8", newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


# ----------------------------------------------------------------------------------------------- frentes


def ler_arquivo(nome: str, chaves_: dict, pat: re.Pattern, abrir=abrir_remoto, casar=None):
    casar = casar or (lambda maiuscula, _crua: pat.search(maiuscula) is not None)
    with abrir(BASE + nome) as texto:
        return filtrar(texto, casar)


def frente_tabela(frente: str, chaves_: dict, pat: re.Pattern, run_id, abrir=abrir_remoto,
                  raiz: pathlib.Path | None = None) -> dict:
    """Registro e CMED: linhas filtradas vão ao público, com a substância achada em cada uma."""
    raiz = raiz or comum.RAIZ
    manifesto = rede.Manifesto("dados_publicos", {"subfrente": frente, "fonte": BASE, "arquivos": ARQUIVOS[frente],
                                                  "filtro": "linha que cita substância ou marca de data/config/termos.json"},
                               run_id)
    saida, total_lido, total_ficou = {"arquivos": []}, 0, 0
    for nome in ARQUIVOS[frente]:
        try:
            cabecalho, linhas, total, _ = ler_arquivo(nome, chaves_, pat, abrir)
        except Exception as erro:
            manifesto.bloqueio(f"{nome}: {type(erro).__name__}: {erro}")
            saida["arquivos"].append({"arquivo": nome, "url": BASE + nome, "linhas_no_arquivo": None, "erro": str(erro)[:200]})
            continue
        total_lido += total
        total_ficou += len(linhas)
        registros = [dict(zip(cabecalho, l)) | {"_substancias": substancias_da_linha(l, chaves_, pat)} for l in linhas]
        ativo = _ou(coluna(cabecalho, "PRINCIPIO"), coluna(cabecalho, "SUBSTANCIA"))
        situacao = coluna(cabecalho, "SITUACAO")
        saida["arquivos"].append({
            "arquivo": nome, "url": BASE + nome, "colunas": cabecalho, "linhas_no_arquivo": total,
            "linhas_que_citam": len(linhas),
            "por_substancia": contar(s for r in registros for s in r["_substancias"]),
            "por_principio_ativo": contar(l[ativo] for l in linhas) if ativo is not None else None,
            "por_situacao": contar(l[situacao] for l in linhas) if situacao is not None else None,
            "linhas": registros})
        print(f"{frente} {nome}: {total} linhas, {len(linhas)} citam as substâncias")
    destino = raiz / "data" / "dados_publicos" / f"{frente}.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": run_id,
                           "nota": "Dados de empresas e produtos, como a Anvisa publica. Filtro por substância e marca.",
                           **saida})
    manifesto.arquivo(destino, raiz)
    leu = any(a.get("linhas_no_arquivo") is not None for a in saida["arquivos"])
    manifesto.dados.update({
        "universo": {"valor": total_lido if leu else None, "fonte": "linhas dos arquivos da Anvisa, contadas na leitura"},
        "lido": total_lido if leu else None,
        "amostra": {"n": total_ficou if leu else None, "como": "linhas que citam substância ou marca"},
        "parou_por": "arquivo_inteiro" if leu else None})
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: {frente}, {total_ficou} de {total_lido} linhas")
    return saida


def frente_vigimed(chaves_: dict, pat: re.Pattern, run_id, privado: pathlib.Path, abrir=abrir_remoto,
                   raiz: pathlib.Path | None = None) -> dict:
    """Notificações em que uma das substâncias aparece entre os medicamentos. Linhas só no privado."""
    raiz = raiz or comum.RAIZ
    manifesto = rede.Manifesto("dados_publicos", {"subfrente": "vigimed", "fonte": BASE, "arquivos": ARQUIVOS["vigimed"],
                                                  "filtro": "notificação com medicamento que cita substância ou marca"},
                               run_id)
    pasta = privado / "dados_publicos" / "vigimed"
    resultado: dict = {"arquivos": []}
    try:
        cab_m, med, total_m, _ = ler_arquivo("VigiMed_Medicamentos.csv", chaves_, pat, abrir)
    except Exception as erro:
        manifesto.bloqueio(f"VigiMed_Medicamentos.csv: {type(erro).__name__}: {erro}")
        manifesto.gravar(raiz)
        print(f"BLOQUEADO vigimed: {erro}")
        return resultado
    id_m = _indice_id(cab_m)
    relacao = _ou(coluna(cab_m, "RELACAO"), coluna(cab_m, "SUSPEIT"))
    gravar_csv(pasta / "medicamentos.csv", cab_m, med)
    manifesto.arquivo(pasta / "medicamentos.csv", privado, privado=True)
    por_id: dict[str, set] = collections.defaultdict(set)
    for linha in med:
        for s in substancias_da_linha(linha, chaves_, pat):
            por_id[linha[id_m].strip()].add(s)
    ids = set(por_id)
    resultado["arquivos"].append({"arquivo": "VigiMed_Medicamentos.csv", "colunas": cab_m, "linhas_no_arquivo": total_m,
                                  "linhas_que_citam": len(med),
                                  "relacao_com_o_evento": contar(l[relacao] for l in med) if relacao is not None else None})
    print(f"vigimed medicamentos: {total_m} linhas, {len(med)} citam, {len(ids)} notificações")

    def casar_id(indice: int, sep: str):
        def casar(_maiuscula: str, crua: str) -> bool:
            if indice == 0:
                return crua.split(sep, 1)[0].strip().strip('"') in ids
            campos = next(csv.reader([crua], delimiter=sep))
            return len(campos) > indice and campos[indice].strip() in ids
        return casar
    tabelas = {}
    for nome, rotulo in (("VigiMed_Notificacoes.csv", "notificacoes"), ("VigiMed_Reacoes.csv", "reacoes")):
        try:
            with abrir(BASE + nome) as texto:
                linhas_iter = iter(texto)
                primeira = next(linhas_iter, "")
                sep = separador(primeira)
                cab = [c.strip().strip('"').lstrip("\ufeff") for c in next(csv.reader([primeira], delimiter=sep))]
                indice = _indice_id(cab)
                cab, linhas, total, _ = filtrar(_com_cabecalho(primeira, linhas_iter), casar_id(indice, sep))
        except Exception as erro:
            manifesto.bloqueio(f"{nome}: {type(erro).__name__}: {erro}")
            resultado["arquivos"].append({"arquivo": nome, "linhas_no_arquivo": None, "erro": str(erro)[:200]})
            continue
        gravar_csv(pasta / f"{rotulo}.csv", cab, linhas)
        manifesto.arquivo(pasta / f"{rotulo}.csv", privado, privado=True)
        tabelas[rotulo] = (cab, linhas, indice)
        resultado["arquivos"].append({"arquivo": nome, "colunas": cab, "linhas_no_arquivo": total, "linhas_que_citam": len(linhas)})
        print(f"vigimed {rotulo}: {total} linhas, {len(linhas)} das notificações filtradas")
    resultado.update(agregar_vigimed(por_id, tabelas))
    destino = raiz / "data" / "dados_publicos" / "vigimed.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": run_id,
                           "nota": ("Notificações espontâneas de suspeita de evento adverso. Notificação não prova que o "
                                    "medicamento causou o evento. Contagem menor que 5 aparece como '<5'. "
                                    "As linhas por paciente ficam só no repositório privado."),
                           **resultado})
    manifesto.arquivo(destino, raiz)
    manifesto.dados.update({
        "universo": {"valor": total_m, "fonte": "linhas de VigiMed_Medicamentos.csv (um medicamento por linha), contadas na leitura"},
        "lido": total_m, "amostra": {"n": len(ids), "como": "notificações com ao menos um medicamento que cita substância ou marca"},
        "parou_por": "arquivo_inteiro"})
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: vigimed, {len(ids)} notificações")
    return resultado


def _indice_id(cab: list[str]) -> int:
    for pedacos in (("IDENTIFICACAO", "NOTIFICACAO"), ("ID", "NOTIFICACAO"), ("IDENTIFICACAO",), ("NOTIFICACAO",)):
        i = coluna(cab, *pedacos, evitar=("DATA", "TIPO"))
        if i is not None:
            return i
    return 0


def _com_cabecalho(primeira: str, resto):
    yield primeira
    yield from resto


def _ano_da_linha(linha: list[str], indices: list[int]) -> str | None:
    """Ano da primeira coluna de data preenchida, na ordem dada."""
    for i in indices:
        if i < len(linha):
            ano = _ano(linha[i])
            if ano:
                return ano
    return None


def _ano(texto: str) -> str | None:
    m = re.search(r"(19|20)\d{2}", texto or "")
    if not m:
        return None
    # dd/mm/aaaa, aaaa-mm-dd ou aaaamm
    return m.group(0)


def agregar_vigimed(por_id: dict[str, set], tabelas: dict) -> dict:
    saida: dict = {"notificacoes": len(por_id), "por_substancia": contar(s for v in por_id.values() for s in v)}
    if "notificacoes" in tabelas:
        cab, linhas, ind = tabelas["notificacoes"]
        datas = [i for i in (coluna(cab, "DATA", "NOTIFICACAO"), coluna(cab, "DATA", "RECEB"), coluna(cab, "DATA", "INCLUSAO"))
                 if i is not None]
        data = datas[0] if datas else None
        campos = {"por_ano": data, "por_uf": coluna(cab, "UF"), "por_sexo": coluna(cab, "SEXO"),
                  "por_faixa_etaria": _ou(coluna(cab, "GRUPO", "IDADE"), coluna(cab, "FAIXA")),
                  "por_gravidade": coluna(cab, "GRAVE", evitar=("DESCR",)), "por_quem_notificou": _ou(coluna(cab, "NOTIFICADOR"), coluna(cab, "RECEBIDO"))}
        for rotulo, i in campos.items():
            if i is None:
                saida[rotulo] = None
                continue
            valores = (_ano_da_linha(l, datas) if rotulo == "por_ano" else l[i].strip() for l in linhas if len(l) > i)
            saida[rotulo] = sorted(contar(valores), key=lambda x: x["valor"]) if rotulo == "por_ano" else contar(valores)
        if data is not None:
            ano_sub = collections.Counter()
            for l in linhas:
                if len(l) > max(ind, data):
                    for s in por_id.get(l[ind].strip(), ()):
                        ano_sub[(_ano_da_linha(l, datas) or "não informado", s)] += 1
            saida["por_ano_e_substancia"] = [{"ano": a, "substancia": s, "n": n if n >= MINIMO_PUBLICO else f"<{MINIMO_PUBLICO}"}
                                             for (a, s), n in sorted(ano_sub.items())]
        saida["colunas_usadas"] = {k: (cab[v] if v is not None else None) for k, v in campos.items()}
        saida["colunas_usadas"]["por_ano"] = " , senão ".join(cab[i] for i in datas) if datas else None
    if "reacoes" in tabelas:
        cab, linhas, _ = tabelas["reacoes"]
        pt = _ou(coluna(cab, "PT"), coluna(cab, "REACAO", evitar=("DATA", "DESF", "GRAV")), coluna(cab, "EVENTO"))
        saida["reacoes_mais_notificadas"] = contar(l[pt].strip() for l in linhas if pt is not None and len(l) > pt)[:TOPO] if pt is not None else None
        saida["coluna_da_reacao"] = cab[pt] if pt is not None else None
    return saida


def meses_sngpc(tipo: str, inicio: str, leitor=sondar_fontes.baixar) -> list[tuple[str, str]]:
    """(aaaamm, url) dos meses publicados a partir do início do período lido."""
    pagina = leitor(SNGPC[tipo])
    if pagina.get("http") != 200:
        raise RuntimeError(f"índice do SNGPC: {pagina.get('erro') or pagina.get('http')}")
    itens = sondar_fontes.ler_indice(pagina["corpo"].decode("utf-8", "replace"), SNGPC[tipo])
    saida = []
    for item in itens:
        m = re.search(r"_(\d{6})\.csv$", item["nome"], re.I)
        if m and m.group(1) >= inicio:
            saida.append((m.group(1), item["url"]))
    return sorted(saida)


def frente_sngpc(tipo: str, chaves_: dict, pat: re.Pattern, run_id, privado: pathlib.Path, inicio: str,
                 abrir=abrir_remoto, leitor=sondar_fontes.baixar, raiz: pathlib.Path | None = None) -> dict:
    raiz = raiz or comum.RAIZ
    manifesto = rede.Manifesto("dados_publicos", {"subfrente": f"sngpc_{tipo}", "fonte": SNGPC[tipo],
                                                  "filtro": "linha que cita substância ou marca", "meses_desde": inicio},
                               run_id)
    try:
        meses = meses_sngpc(tipo, inicio, leitor)
    except Exception as erro:
        manifesto.bloqueio(f"índice: {type(erro).__name__}: {erro}")
        manifesto.gravar(raiz)
        print(f"BLOQUEADO sngpc {tipo}: {erro}")
        return {}
    pasta = privado / "dados_publicos" / f"sngpc_{tipo}"
    por_mes, linhas_todas, cab_final, total_lido = [], [], None, 0
    for aaaamm, url in meses:
        try:
            with abrir(url, tempo=300) as texto:
                cab, linhas, total, _ = filtrar(texto, lambda maiuscula, _crua: pat.search(maiuscula) is not None)
        except Exception as erro:
            manifesto.bloqueio(f"{aaaamm}: {type(erro).__name__}: {erro}")
            por_mes.append({"mes": aaaamm, "linhas_no_arquivo": None, "erro": str(erro)[:200]})
            continue
        total_lido += total
        cab_final = cab
        # um arquivo comprimido por mês: o GitHub recusa arquivo acima de 100 MB
        gravar_csv(pasta / f"{aaaamm}.csv.gz", cab, linhas)
        manifesto.arquivo(pasta / f"{aaaamm}.csv.gz", privado, privado=True)
        linhas_todas += [[aaaamm] + l for l in linhas]
        por_mes.append({"mes": aaaamm, "linhas_no_arquivo": total, "linhas_que_citam": len(linhas)})
        print(f"sngpc {tipo} {aaaamm}: {total} linhas, {len(linhas)} citam", flush=True)
    resultado = {"tipo": tipo, "meses": por_mes, "colunas": cab_final}
    if cab_final:
        cab = ["ARQUIVO_MES"] + cab_final
        resultado.update(agregar_sngpc(cab, linhas_todas, chaves_, pat))
    destino = raiz / "data" / "dados_publicos" / f"sngpc_{tipo}.json"
    comum.gravar(destino, {"obtido_em": manifesto.dados["iniciado_em"], "run_id": run_id,
                           "nota": ("Vendas registradas no SNGPC, como a Anvisa publica. Contagem menor que 5 aparece como '<5'. "
                                    "As linhas ficam só no repositório privado."), **resultado})
    manifesto.arquivo(destino, raiz)
    leu = any(m.get("linhas_no_arquivo") is not None for m in por_mes)
    manifesto.dados.update({
        "universo": {"valor": total_lido if leu else None,
                     "fonte": f"linhas dos arquivos mensais do SNGPC ({tipo}) publicados a partir de {inicio}, contadas na leitura"},
        "lido": total_lido if leu else None,
        "amostra": {"n": len(linhas_todas) if leu else None, "como": "linhas que citam substância ou marca"},
        "parou_por": "arquivo_inteiro" if leu else None})
    print(f"gravado {manifesto.gravar(raiz).relative_to(raiz)}: sngpc {tipo}, {len(linhas_todas)} linhas")
    return resultado


def _numero(texto: str) -> float:
    try:
        return float((texto or "0").replace(".", "").replace(",", ".")) if "," in (texto or "") else float(texto or 0)
    except ValueError:
        return 0.0


def agregar_sngpc(cab: list[str], linhas: list[list[str]], chaves_: dict, pat: re.Pattern) -> dict:
    ano = coluna(cab, "ANO")
    mes = coluna(cab, "MES", evitar=("ARQUIVO",))
    qtd = _ou(coluna(cab, "QT", "VENDIDA"), coluna(cab, "QT_UNIDADE"), coluna(cab, "QTD", "VEND"), coluna(cab, "QTD"))
    ativo = coluna(cab, "PRINCIPIO")
    uf = _ou(coluna(cab, "UF", "VENDA"), coluna(cab, "UF", evitar=("CONSELHO",)))
    sexo, idade = coluna(cab, "SEXO"), coluna(cab, "IDADE", evitar=("UNIDADE",))
    mes_sub, qtd_sub, qtd_uf = collections.Counter(), collections.Counter(), collections.Counter()
    for l in linhas:
        subs = substancias_da_linha([l[ativo]] if ativo is not None and len(l) > ativo else l, chaves_, pat) or ["outra"]
        chave_mes = (f"{l[ano]}-{int(l[mes]):02d}" if ano is not None and mes is not None and l[mes].strip().isdigit()
                     else l[0][:4] + "-" + l[0][4:])
        q = _numero(l[qtd]) if qtd is not None and len(l) > qtd else 1
        for s in subs:
            mes_sub[(chave_mes, s)] += 1
            qtd_sub[(chave_mes, s)] += q
        if uf is not None and len(l) > uf:
            qtd_uf[l[uf].strip()] += q
    return {
        "por_mes_e_substancia": [{"mes": m, "substancia": s, "linhas": n if n >= MINIMO_PUBLICO else f"<{MINIMO_PUBLICO}",
                                  "quantidade": round(qtd_sub[(m, s)], 2) if n >= MINIMO_PUBLICO else None}
                                 for (m, s), n in sorted(mes_sub.items())],
        "quantidade_por_uf": [{"uf": k, "quantidade": round(v, 2)} for k, v in qtd_uf.most_common()],
        "por_sexo": contar(l[sexo].strip() for l in linhas if sexo is not None and len(l) > sexo) if sexo is not None else None,
        "por_idade": contar(l[idade].strip() for l in linhas if idade is not None and len(l) > idade)[:40] if idade is not None else None,
        "colunas_usadas": {"ano": _nome(cab, ano), "mes": _nome(cab, mes), "quantidade": _nome(cab, qtd),
                           "principio_ativo": _nome(cab, ativo), "uf": _nome(cab, uf), "sexo": _nome(cab, sexo),
                           "idade": _nome(cab, idade)},
    }


def _nome(cab, i):
    return cab[i] if i is not None else None


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Dados abertos da Anvisa sobre as substâncias das canetas.")
    leitor.add_argument("--frentes", nargs="+", default=["registro", "cmed", "vigimed", "sngpc"])
    leitor.add_argument("--privado", type=pathlib.Path, required=True)
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    chaves_ = chaves()
    pat = padrao(chaves_)
    inicio, _ = rede.periodo_lido()
    ok = 0
    for frente in opcoes.frentes:
        try:
            if frente in ("registro", "cmed"):
                frente_tabela(frente, chaves_, pat, opcoes.run_id)
            elif frente == "vigimed":
                frente_vigimed(chaves_, pat, opcoes.run_id, opcoes.privado)
            elif frente == "sngpc":
                for tipo in SNGPC:
                    frente_sngpc(tipo, chaves_, pat, opcoes.run_id, opcoes.privado, inicio.strftime("%Y%m"))
            ok += 1
        except Exception as erro:
            print(f"ERRO {frente}: {type(erro).__name__}: {rede.sem_chave(str(erro))}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
