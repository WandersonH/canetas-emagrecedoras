"""Reconciliação com a Apify: execuções feitas e pagas que não estão em nenhum manifesto.

Quando um workflow é interrompido (tempo limite, cancelamento), as execuções na Apify já aconteceram e foram cobradas,
mas o manifesto da rede não chegou a ser gravado. Este script:
1. lista as execuções de cada ator de data/config/coleta.json desde --desde (lista do ator, não é consulta de saldo);
2. ignora as que já estão em algum manifesto (pelo ID da execução);
3. aborta as que ainda estiverem rodando (elas têm teto próprio, mas não servem mais a nenhuma coleta);
4. baixa os itens de cada execução, grava bruto e tabela no privado e um manifesto por rede, com o custo de cada
   execução, na etapa indicada.
Assim a trava de gasto volta a enxergar todo o dinheiro gasto, e o que já foi pago não é coletado de novo.

Uso: python scripts/reconciliar_apify.py --desde 2026-11-23T21:19:00Z --etapa publicacoes --privado /caminho --run-id 123
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apify  # noqa: E402
import collect_redes as cr  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402


def runs_em_manifestos() -> set[str]:
    ids = set()
    for caminho in comum.MANIFESTOS.glob("*.json"):
        m = comum.carregar(caminho)
        for t in (m.get("consulta") or {}).get("por_termo") or []:
            if t.get("run"):
                ids.add(t["run"])
        for r in (m.get("consulta") or {}).get("execucoes") or []:
            ids.add(r["run"])
    return ids


def termo_da_entrada(rede_id: str, entrada: dict, termos: list[str]) -> str | None:
    if rede_id == "tiktok":
        return (entrada.get("keywords") or [None])[0]
    if rede_id == "instagram":
        tag = (entrada.get("hashtags") or [None])[0]
        return next((t for t in termos if cr.hashtag(t) == tag), tag)
    if rede_id == "x":
        busca = (entrada.get("searchTerms") or [""])[0]
        return busca.split('"')[1] if busca.count('"') >= 2 else busca
    if rede_id == "kwai":
        return (entrada.get("searchTerms") or [None])[0]
    return None


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Reconcilia execuções da Apify sem manifesto.")
    leitor.add_argument("--desde", required=True, help="início, em UTC, no formato 2026-11-23T21:19:00Z")
    leitor.add_argument("--etapa", required=True)
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--run-id", default=None)
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    coleta = comum.config("coleta")
    token = os.environ.get(coleta["apify"]["segredo"], "").strip()
    if not token:
        print("BLOQUEADO: token ausente")
        return 1
    inicio, fim = rede.periodo_lido()
    termos = [t["termo"] for t in rede.termos_de_busca()]
    conhecidos = runs_em_manifestos()
    total = 0.0
    for rede_id, cfg in coleta["pagas"].items():
        ator = cfg["ator"]
        lista = apify.api("GET", f"/acts/{ator}/runs?desc=1&limit=100", token)["data"].get("items") or []
        novos = [r for r in lista if (r.get("startedAt") or "") >= opcoes.desde and r["id"] not in conhecidos]
        if not novos:
            print(f"{rede_id}: nenhuma execução sem manifesto")
            continue
        manifesto = rede.Manifesto(rede_id, {"ator": ator, "reconciliacao": f"execuções desde {opcoes.desde} sem manifesto",
                                             "inicio": inicio.isoformat(), "fim": fim.isoformat()}, opcoes.run_id, etapa=opcoes.etapa)
        execucoes, brutos, linhas = [], [], {}
        for r in sorted(novos, key=lambda x: x.get("startedAt") or ""):
            if r.get("status") in ("READY", "RUNNING"):
                apify.api("POST", f"/actor-runs/{r['id']}/abort", token)
            run = apify.api("GET", f"/actor-runs/{r['id']}", token)["data"]
            try:
                entrada = apify.api("GET", f"/key-value-stores/{run['defaultKeyValueStoreId']}/records/INPUT", token) or {}
            except Exception:
                entrada = {}
            termo = termo_da_entrada(rede_id, entrada, termos) or "?"
            try:
                itens = apify.baixar_itens(token, run["defaultDatasetId"])
            except Exception as erro:
                itens = []
                manifesto.bloqueio(f"{run['id']}: itens não baixados ({type(erro).__name__})")
            custo = apify.custo(run)
            if not custo:  # sem cobrança informada: preço de referência, para a trava não subestimar
                custo = round(cfg["preco"].get("consulta", 0) + cfg["preco"]["item"] * len(itens), 5)
            total += custo
            normais = [l for l in (cr.normalizar(rede_id, x) for x in itens) if l]
            no_periodo = [l for l in normais if l["publicado_em"] and inicio.isoformat() <= l["publicado_em"] <= fim.isoformat()]
            for l in no_periodo:
                linha = linhas.setdefault(l["item_id"], {**l, "termos": []})
                if termo not in linha["termos"]:
                    linha["termos"].append(termo)
            brutos += [{**x, "_termo": termo} for x in itens]
            execucoes.append({"run": run["id"], "termo": termo, "status": run.get("status"), "inicio": run.get("startedAt"),
                              "fim": run.get("finishedAt"), "itens": len(itens), "no_periodo": len(no_periodo), "custo_usd": custo})
            print(f"{rede_id} '{termo}': {run.get('status')}, {len(itens)} itens, {len(no_periodo)} no período, US$ {custo}")
        carimbo = rede.carimbo(manifesto.dados["iniciado_em"])
        bruto = privado / "bruto" / rede_id / f"{opcoes.etapa}_reconciliado_{carimbo}.json"
        bruto.parent.mkdir(parents=True, exist_ok=True)
        bruto.write_text(json.dumps(brutos, ensure_ascii=False), encoding="utf-8")
        manifesto.arquivo(bruto, privado, privado=True)
        tabela = privado / "terceiros" / rede_id / f"{opcoes.etapa}_reconciliado_{carimbo}.csv"
        tabela.parent.mkdir(parents=True, exist_ok=True)
        with open(tabela, "w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=cr.CAMPOS)
            escritor.writeheader()
            for l in linhas.values():
                escritor.writerow({**l, "termos": "|".join(l["termos"])})
        manifesto.arquivo(tabela, privado, privado=True)
        lido = sum(e["itens"] for e in execucoes)
        manifesto.dados.update({
            "consulta": {**manifesto.dados["consulta"], "execucoes": execucoes},
            "universo": {"valor": None, "fonte": "A busca da rede não informa o total de resultados."},
            "lido": lido, "amostra": {"n": len(linhas), "como": "publicações distintas, com data no período lido, das execuções reconciliadas"},
            "parou_por": "limite", "custo_usd": round(sum(e["custo_usd"] for e in execucoes), 5),
        })
        print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {rede_id}, {len(execucoes)} execuções, {len(linhas)} publicações no período")
    print(f"total reconciliado: US$ {round(total, 4)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
