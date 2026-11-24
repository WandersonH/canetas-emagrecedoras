"""Venda irregular nas redes: triagem automática das publicações, comentários e falas transcritas já coletados.

Regra (data/config/livro_de_codigos.json, eixo venda_irregular, e data/config/venda_irregular.json):
- oferta: o texto tem sinal forte de venda (Pix, WhatsApp, "chama no privado", entrega, telefone de contato...);
  link, preço e "a venda" sozinhos não bastam, porque aparecem em notícia e em descrição de vídeo;
- tipo da oferta, quando há sinal de venda: oferta sem receita, produto sem registro (caneta do Paraguai, TG, T.G.,
  T36, Synedica, Tirzec, Lipoless, retatrutida...), manipulado;
- menção a golpe ou falsificação: o texto fala de golpe, fraude, falsificação ou produto falso, com ou sem oferta
  (é relato ou alerta, não oferta).
Sigla com homônimo (TG, T.G., T36) só conta com palavra do tema por perto (caneta, emagrecer, GLP-1, substância).

É triagem automática: a contagem é de candidatos, e a lista para revisão de contexto (regra 11) fica no privado,
com texto e autor. No público, só contagens por tipo, rede e mês, e quantas vezes cada sinal apareceu.
Link de venda, endereço de loja e perfil de vendedor nunca vão ao público.

Universo: textos de redes já coletados (publicações, comentários e falas transcritas) no período das gratuitas.

Uso:
    python scripts/venda_irregular.py --privado DIR --run-id 123
"""
from __future__ import annotations

import argparse
import collections
import csv
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_corpus  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

FONTES_DE_REDE = ("youtube", "tiktok", "instagram", "x", "kwai", "comentario_youtube", "comentario_tiktok",
                  "comentario_instagram", "comentario_x", "transcricao_tiktok", "transcricao_kwai", "transcricao_youtube")


FRACOS = {"link", "preço em reais", "a venda"}


def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()


def regras(raiz: pathlib.Path | None = None) -> dict:
    cfg = comum.config("venda_irregular", raiz)
    return {nome: re.compile("|".join(cfg["sinais"][nome]), re.IGNORECASE) for nome in cfg["sinais"]}


def rotulo(sinal: str) -> str:
    """Link, telefone e preço viram rótulo: o número ou endereço nunca sai daqui."""
    if sinal.startswith("wa.me"):
        return "link de WhatsApp"
    if re.match(r"https?://", sinal):
        return "link"
    if re.search(r"\d{4}", sinal):
        return "telefone"
    if sinal.startswith("r$"):
        return "preço em reais"
    return sinal


def classificar(texto: str, rs: dict) -> dict:
    """Sinais achados e tipos atribuídos a um texto."""
    t = sem_acento(texto)
    achados = {nome: sorted({rotulo(m.group(0).strip().lower()) for m in r.finditer(t)}) for nome, r in rs.items()}
    if not achados.get("tema"):  # sigla com homônimo só vale com o tema por perto
        achados["produto_sem_registro"] = [x for x in achados.get("produto_sem_registro", [])
                                           if x not in ("tg", "t.g.", "t36", "t.g")]
    # link, preço e "a venda" sozinhos aparecem em notícia e descrição de vídeo: só reforçam, não bastam
    oferta = any(x not in FRACOS for x in achados.get("oferta", []))
    tipos = []
    if oferta and achados.get("sem_receita"):
        tipos.append("oferta sem receita")
    if oferta and achados.get("produto_sem_registro"):
        tipos.append("produto sem registro")
    if oferta and achados.get("manipulado"):
        tipos.append("manipulado")
    if achados.get("golpe"):
        tipos.append("menção a golpe ou falsificação")
    return {"oferta": oferta, "tipos": tipos, "sinais": {k: v for k, v in achados.items() if v and k != "tema"}}


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Triagem automática de venda irregular.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    inicio, fim = (d.isoformat() for d in rede.periodo_lido(gratuita=True))
    rs = regras()
    ts = [t for t in build_corpus.textos(privado, inicio, fim, limpo=False) if t["fonte"] in FONTES_DE_REDE]
    manifesto = rede.Manifesto("venda_irregular", {"fontes": list(FONTES_DE_REDE), "inicio": inicio, "fim": fim,
                                                   "regras": "data/config/venda_irregular.json"}, opcoes.run_id)
    por_fonte = collections.Counter(t["fonte"] for t in ts)
    tipo_rede, tipo_mes, sinais, candidatos = collections.Counter(), collections.Counter(), collections.Counter(), []
    com_oferta = collections.Counter()
    for t in ts:
        c = classificar(t["texto"], rs)
        if c["oferta"] and any(k in c["sinais"] for k in ("sem_receita", "produto_sem_registro", "manipulado")):
            com_oferta[t["fonte"]] += 1
        if not c["tipos"]:
            continue
        for tipo in c["tipos"]:
            tipo_rede[(tipo, t["fonte"])] += 1
            tipo_mes[(tipo, t["data"][:7])] += 1
        for grupo, palavras in c["sinais"].items():
            for p in palavras:
                sinais[(grupo, p)] += 1
        candidatos.append({"fonte": t["fonte"], "id": t["id"], "data": t["data"], "autor": t["autor"],
                           "tipos": "|".join(c["tipos"]), "sinais": "; ".join(f"{k}: {', '.join(v)}" for k, v in c["sinais"].items()),
                           "texto": t["texto"], "revisao": ""})
    carimbo = rede.carimbo(manifesto.dados["iniciado_em"])
    tabela = privado / "terceiros" / "venda_irregular" / f"candidatos_{carimbo}.csv"
    tabela.parent.mkdir(parents=True, exist_ok=True)
    with tabela.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(candidatos[0]) if candidatos else ["fonte"])
        escritor.writeheader()
        escritor.writerows(candidatos)
    manifesto.arquivo(tabela, privado, privado=True)
    destino = comum.RAIZ / "data" / "venda" / "agregado.json"
    comum.gravar(destino, {
        "obtido_em": manifesto.dados["iniciado_em"], "run_id": opcoes.run_id, "periodo": {"inicio": inicio, "fim": fim},
        "nota": ("Triagem automática por palavras e sinais de venda (data/config/venda_irregular.json). São candidatos: "
                 "a revisão de contexto de cada um está pendente. Link de venda, endereço de loja e perfil de vendedor "
                 "ficam fora desta página."),
        "textos_examinados_por_fonte": dict(por_fonte), "textos_examinados": len(ts), "candidatos": len(candidatos),
        "por_tipo_e_fonte": [{"tipo": a, "fonte": b, "n": n} for (a, b), n in sorted(tipo_rede.items())],
        "por_tipo_e_mes": [{"tipo": a, "mes": b, "n": n} for (a, b), n in sorted(tipo_mes.items())],
        "sinais": [{"grupo": a, "sinal": b, "n": n} for (a, b), n in sinais.most_common(80)],
        "revisados": 0})
    manifesto.arquivo(destino, comum.RAIZ)
    manifesto.dados.update({
        "universo": {"valor": len(ts), "fonte": "textos de redes já coletados no período (publicações, comentários e falas)"},
        "lido": len(ts), "amostra": {"n": len(candidatos), "como": "candidatos da triagem automática, revisão pendente"},
        "parou_por": "lista_inteira"})
    print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: venda irregular, {len(candidatos)} candidatos em {len(ts)} textos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
