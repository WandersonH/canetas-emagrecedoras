"""Corpus do estudo, CHD de Reinert, similitude, redes para o Gephi e mapa de emojis.

Fontes (cada texto com a fonte e o mês como variáveis):
- YouTube: título e descrição dos vídeos (privado: terceiros/youtube/*.csv);
- TikTok, Instagram, X e Kwai: texto da publicação (privado: terceiros/<rede>/publicacoes_*.csv);
- imprensa: título das notícias (público: data/imprensa/resultados.json);
- checagens: título das checagens (público: data/checagens/checagens.json).

Privacidade: texto de terceiros vai ao público só anonimizado (scripts/anonimizar.py: sem perfil, link, telefone,
e-mail e números), sem conta e sem link, com o autor trocado por código. A tabela autor → código fica no privado.
Imprensa e checagens são publicações de veículos e agências: título, veículo e link aparecem.

Amostra para a CHD: a matriz da CHD é densa; acima de MAX_SEGMENTOS segmentos, a CHD usa uma amostra aleatória
estratificada por fonte (semente fixa), registrada no JSON com o total. O corpus exportado para o IRaMuTeQ é completo.

Saídas públicas: data/corpus/{canetas_iramuteq.txt, segmentos.json, chd.json, similitude.gexf},
data/redes/{palavras,fontes_termos}.gexf, data/redes/desenhos.json, data/emojis.json.

Uso: python scripts/build_corpus.py --privado /caminho
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import glob
import json
import pathlib
import random
import re
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anonimizar  # noqa: E402
import chd_reinert as cr  # noqa: E402
import comum  # noqa: E402
import redes  # noqa: E402

PALAVRAS_SEGMENTO = 40
MAX_SEGMENTOS = 12000
SEMENTE = 2026
FONTES = ("youtube", "tiktok", "instagram", "x", "kwai", "comentario_youtube", "comentario_tiktok", "comentario_instagram",
          "comentario_x", "transcricao_tiktok", "transcricao_kwai", "transcricao_youtube", "imprensa", "checagens")
csv.field_size_limit(10 ** 8)


def ler_csv(caminho) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def limpar(texto: str) -> str:
    texto = cr.normalizar_risadas(re.sub(r"https?://\S+|www\.\S+", " ", texto or ""))
    return " ".join(texto.replace("*", " ").replace("$", " ").split())


DISFARCE = re.compile(r"(?<=[a-zà-ú])[@4](?=[a-zà-ú])|(?<=[a-zà-ú])0(?=[a-zà-ú])|(?<=[a-zà-ú])[1!](?=[a-zà-ú])|(?<=[a-zà-ú])3(?=[a-zà-ú])", re.I)
TROCA = {"@": "a", "4": "a", "0": "o", "1": "i", "!": "i", "3": "e"}


def sem_disfarce(texto: str) -> str:
    """Desfaz grafias que trocam letra por símbolo para driblar moderação (Mounj@ro, tirzep@tida, 0zempic → letras).
    Só para a análise; o texto exibido no corpus fica como foi publicado."""
    return DISFARCE.sub(lambda m: TROCA[m.group(0)], texto)


def segmentar(texto: str, n: int = PALAVRAS_SEGMENTO) -> list[str]:
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto) if f.strip()]
    segs, atual = [], []
    for frase in frases:
        ws = frase.split()
        while len(ws) > n * 1.5:
            if atual:
                segs.append(" ".join(atual))
                atual = []
            segs.append(" ".join(ws[:n]))
            ws = ws[n:]
        atual += ws
        if len(atual) >= n:
            segs.append(" ".join(atual))
            atual = []
    if atual:
        segs.append(" ".join(atual))
    return segs


def textos(privado: pathlib.Path, inicio: str, fim: str, limpo: bool = True) -> list[dict]:
    """Um registro por publicação, sem repetição, dentro do período lido. limpo=False guarda o texto cru
    (com links e cifrões), para quem precisa dos sinais de venda."""
    vistos, saida = set(), []

    def add(fonte, chave, data, texto, autor, termos, publico_url=None, veiculo=None):
        data = (data or "")[:10]
        if not data or not (inicio <= data <= fim) or (fonte, chave) in vistos:
            return
        texto = limpar(texto) if limpo else " ".join((texto or "").split())
        if len(texto.split()) < 3:
            return
        vistos.add((fonte, chave))
        saida.append({"fonte": fonte, "id": chave, "data": data, "texto": texto, "autor": autor or "", "termos": termos,
                      "url": publico_url, "veiculo": veiculo})

    for caminho in sorted(glob.glob(str(privado / "terceiros" / "youtube" / "*.csv"))):
        for r in ler_csv(caminho):
            add("youtube", r["video_id"], r.get("publicado_em"), f"{r.get('titulo') or ''}. {r.get('descricao') or ''}",
                r.get("canal_id"), (r.get("termos") or "").split("|"))
    for rede_id in ("tiktok", "instagram", "x", "kwai"):
        for caminho in sorted(glob.glob(str(privado / "terceiros" / rede_id / "*.csv"))):
            for r in ler_csv(caminho):
                add(rede_id, r["item_id"], r.get("publicado_em"), r.get("texto"), r.get("conta"), (r.get("termos") or "").split("|"))
    imp = comum.RAIZ / "data" / "imprensa" / "resultados.json"
    if imp.exists():
        for n in comum.carregar(imp)["noticias"]:
            add("imprensa", n["link"], n.get("data"), n.get("titulo"), n.get("veiculo"), n.get("termos") or [], n["link"], n.get("veiculo"))
    for rede_id in ("youtube", "tiktok", "instagram", "x"):  # comentários: texto e autor só no privado
        for caminho in sorted(glob.glob(str(privado / "terceiros" / "comentarios" / rede_id / "*.csv"))):
            for r in ler_csv(caminho):
                add(f"comentario_{rede_id}", r["comentario_id"], r.get("publicado_em"), r.get("texto"), r.get("autor"), [])
    for rede_id in ("tiktok", "kwai", "youtube"):  # fala transcrita dos vídeos: só no privado
        for caminho in sorted(glob.glob(str(privado / "terceiros" / "transcricoes" / rede_id / "*.csv"))):
            for r in ler_csv(caminho):
                add(f"transcricao_{rede_id}", r["item_id"], r.get("publicado_em"), r.get("texto"), r.get("conta"), [])
    ag = comum.RAIZ / "data" / "checagens" / "agencias.json"
    if ag.exists():
        for c in comum.carregar(ag)["checagens"]:
            if c.get("checagem") is False:
                continue
            add("checagens", c["link"], c.get("data"), c.get("titulo"), c.get("agencia"), c.get("grupos") or [], c["link"],
                c.get("agencia"))
    chk = comum.RAIZ / "data" / "checagens" / "checagens.json"
    if chk.exists():
        for c in comum.carregar(chk)["checagens"]:
            add("checagens", c["link"], c.get("data"), f"{c.get('titulo') or ''}. {c.get('alegacao') or ''}", c.get("agencia"),
                c.get("termos") or [], c["link"], c.get("agencia"))
    return saida


IDIOMAS = {
    "pt": set("o a os as de do da dos das em no na nos nas que com para por um uma não é e se mais como foi são ou ao seu sua isso esse essa você eu meu minha muito".split()),
    "es": set("el la los las de del en que con para por un una no es y se más como fue son o al su esto ese esa usted yo mi muy".split()),
    "en": set("the a of to in on for with is are was it this that you my and or not how what your be have do".split()),
}


def idioma(texto: str) -> str:
    """Idioma provável pelo número de palavras vazias de cada língua. Empate ou nenhuma: 'pt' (texto curto fica)."""
    ws = re.findall(r"[a-záéíóúâêôãõçñü]+", texto.lower())
    conta = {lingua: sum(1 for w in ws if w in vazias) for lingua, vazias in IDIOMAS.items()}
    melhor = max(conta, key=lambda k: (conta[k], k == "pt"))
    return melhor if conta[melhor] > conta["pt"] else "pt"


def publico(t: dict, codigos: dict) -> dict:
    """Versão pública de um texto: terceiros anonimizados, sem conta e sem link."""
    if t["fonte"] in ("imprensa", "checagens"):
        return {"texto": t["texto"], "autor": t["veiculo"] or "", "url": t["url"]}
    return {"texto": anonimizar.anonimizar_texto(t["texto"]), "autor": codigos.get(t["autor"].strip().lower(), ""), "url": None}


def amostra_estratificada(n_por_fonte: dict, maximo: int, rng) -> dict:
    total = sum(n_por_fonte.values())
    if total <= maximo:
        return {f: list(range(n)) for f, n in n_por_fonte.items()}
    return {f: sorted(rng.sample(range(n), max(1, round(n * maximo / total)))) for f, n in n_por_fonte.items()}


def chd(segs: list[dict]) -> tuple[dict, np.ndarray, list[str], np.ndarray]:
    X, voc = cr.matriz([sem_disfarce(s["t"]) for s in segs])
    n_ativos = int((X.sum(1) > 0).sum())
    mc = max(cr.MIN_CLASSE, int(cr.MIN_CLASSE_PCT * n_ativos))
    rot, arvore, escolha = cr.chd_iramuteq(X, min_classe=mc, n_textos=len({s["doc"] for s in segs}))
    cl = rot > 0
    n = int(cl.sum())
    Xc, rc, tot = X[cl], rot[cl], X[cl].sum(0)
    fontes = np.array([s["f"] for s in segs])[cl]
    col = {f: j for j, f in enumerate(voc)}
    classes = []
    for k in sorted(set(rc.tolist())):
        m = rc == k
        nk = int(m.sum())
        ch = cr.chi2_assoc(Xc[m].sum(0), tot, nk, n)
        formas = [[voc[j], round(float(ch[j]), 1), int(Xc[m][:, j].sum())] for j in np.argsort(-ch)[:25] if ch[j] >= cr.CHI_CRIT]
        variaveis = {}
        for f in FONTES:
            em = fontes == f
            if not em.any():
                continue
            vch = cr.chi2_assoc(np.array([float((em & m).sum())]), np.array([float(em.sum())]), nk, n)[0]
            variaveis[f"fonte:{f}"] = {"segmentos": int((em & m).sum()), "pct_da_classe": round(100 * (em & m).sum() / nk, 1), "chi2": round(float(vch), 1)}
        idx = np.where(cl)[0][m]
        classes.append({"classe": k, "segmentos": nk, "pct": round(100 * nk / max(1, n), 1), "formas": formas, "variaveis": variaveis,
                        "segmentos_da_classe": [int(i) for i in idx],
                        "segmentos_por_forma": {f[0]: [int(i) for i in idx if X[i, col[f[0]]] > 0] for f in formas}, "nome": None})
    saida = {"metodo": (f"CHD de Reinert (classificação simples): até {cr.K} classes terminais, regra dos 75%, formas com {cr.MIN_FREQ}+ segmentos, "
                        f"classe mínima de {int(cr.MIN_CLASSE_PCT * 100)}% dos segmentos, χ² ≥ {cr.CHI_CRIT}. Segmentos de ~{PALAVRAS_SEGMENTO} palavras. "
                        "Lematização pelo dicionário do IRaMuTeQ. Os nomes das classes são dados pelo pesquisador; conferir no IRaMuTeQ com o corpus exportado."),
             "lematizacao": cr.lematizacao(), "escolha_classes": escolha, "segmentos_classificados": n,
             "pct_classificados": round(100 * n / max(1, len(segs)), 1), "formas_ativas": len(voc),
             "aproveitamento": cr.aproveitamento(rot, len(segs)), "arvore": arvore, "classes": classes}
    return saida, X, voc, rot


def emojis(segs: list[dict]) -> dict:
    import emoji as em
    contagem, onde = collections.Counter(), collections.defaultdict(list)
    for s in segs:
        achados = [e["emoji"] for e in em.emoji_list(s["t"])]
        for e in set(achados):
            onde[e].append(s["i"])
        contagem.update(achados)
    sentimento = {}
    ranking = comum.CONFIG / "emoji_sentiment_ranking_v1.csv"
    if ranking.exists():
        for r in ler_csv(ranking):
            try:
                oc = int(r.get("Occurrences") or 0)
                if oc:
                    sentimento[r["Emoji"]] = round((int(r["Positive"]) - int(r["Negative"])) / oc, 3)
            except (KeyError, ValueError):
                continue
    return {"nota": "Emojis dos textos do corpus. Sentimento: Emoji Sentiment Ranking v1.0 (Kralj Novak et al., 2015); fora do ranking fica ⛔.",
            "ocorrencias": sum(contagem.values()),
            "emojis": [{"emoji": e, "n": n, "segmentos": len(onde[e]), "sentimento": sentimento.get(e), "nome": em.demojize(e, language="pt").strip(":").replace("_", " "),
                        "seg": onde[e][:400]} for e, n in contagem.most_common(120)]}


HASHTAG = re.compile(r"#([0-9a-zà-ÿ_]*[a-zà-ÿ][0-9a-zà-ÿ_]*)", re.IGNORECASE)


def hashtags(ts: list[dict], minimo_textos: int = 5, minimo_autores: int = 3, top: int = 120):
    """Nós = hashtags; aresta = as duas no mesmo texto. Fica a hashtag com uso amplo (textos e autores)."""
    por_texto = [(t, sorted({h.lower() for h in HASHTAG.findall(t["texto"] or "")})) for t in ts]
    n_textos, autores = collections.Counter(), collections.defaultdict(set)
    for t, hs in por_texto:
        for h in hs:
            n_textos[h] += 1
            autores[h].add((t["fonte"], t.get("autor") or ""))
    ficam = {h for h, n in n_textos.items() if n >= minimo_textos and len(autores[h]) >= minimo_autores}
    nos = {h: {"rotulo": "#" + h, "tipo": "hashtag", "n": n_textos[h]} for h in ficam}
    ar = collections.Counter()
    for _, hs in por_texto:
        hs = [h for h in hs if h in ficam]
        for i, a in enumerate(hs):
            for b in hs[i + 1:]:
                ar[(a, b)] += 1
    return nos, dict(ar), (redes._desenho(nos, ar, top) if ar else None)


def volume(ts: list[dict]) -> dict:
    """Textos do corpus por fonte e mês (agregado)."""
    saida: dict = collections.defaultdict(collections.Counter)
    for t in ts:
        if t.get("data"):
            saida[t["fonte"]][t["data"][:7]] += 1
    return {"nota": "Textos do corpus (depois do filtro de idioma) por fonte e mês de publicação.",
            "por_fonte": {f: dict(sorted(c.items())) for f, c in saida.items()}}


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Corpus, CHD, similitude, redes e emojis.")
    leitor.add_argument("--privado", required=True)
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    janela = comum.config("projeto")["janelas"]["periodo_lido"]
    inicio = datetime.datetime.strptime(janela["inicio"], "%d/%m/%Y").date().isoformat()
    fim = datetime.date.today().isoformat() if not janela.get("fim") else datetime.datetime.strptime(janela["fim"], "%d/%m/%Y").date().isoformat()
    lidos = textos(privado, inicio, fim)
    fora = collections.Counter()
    ts = []
    for t in lidos:
        lingua = idioma(t["texto"])
        if lingua == "pt":
            ts.append(t)
        else:
            fora[(t["fonte"], lingua)] += 1
    if not ts:
        print("⛔ corpus vazio")
        return 1
    codigos = anonimizar.codigos_de_autores([t["autor"] for t in ts if t["fonte"] not in ("imprensa", "checagens")])
    comum.gravar(privado / "codigos" / "autores.json", codigos)
    pasta = comum.RAIZ / "data" / "corpus"
    pasta.mkdir(parents=True, exist_ok=True)
    pub = [publico(t, codigos) for t in ts]
    with open(pasta / "canetas_iramuteq.txt", "w", encoding="utf-8") as arquivo:
        for t, p in sorted(zip(ts, pub), key=lambda x: (x[0]["fonte"], x[0]["data"])):
            arquivo.write(f"**** *fonte_{t['fonte']} *mes_{t['data'][:7].replace('-', '')}\n{p['texto']}\n\n")
    with open(privado / "terceiros" / "corpus_iramuteq_original.txt", "w", encoding="utf-8") as arquivo:
        for t in sorted(ts, key=lambda x: (x["fonte"], x["data"])):
            arquivo.write(f"**** *fonte_{t['fonte']} *mes_{t['data'][:7].replace('-', '')}\n{t['texto']}\n\n")
    # segmentos (texto público) e amostra da CHD
    todos = []
    for doc, (t, p) in enumerate(zip(ts, pub)):
        for s in segmentar(p["texto"]):
            todos.append({"doc": doc, "f": t["fonte"], "d": t["data"], "a": p["autor"], "u": p["url"], "t": s,
                          "k": "|".join(x for x in t["termos"] if x)})
    por_fonte = collections.defaultdict(list)
    for s in todos:
        por_fonte[s["f"]].append(s)
    rng = random.Random(SEMENTE)
    escolha = amostra_estratificada({f: len(v) for f, v in por_fonte.items()}, MAX_SEGMENTOS, rng)
    segs = [por_fonte[f][i] for f in FONTES if f in escolha for i in escolha[f]]
    for i, s in enumerate(segs):
        s["i"] = i
    resultado, X, voc, rot = chd(segs)
    resultado.update({
        "gerado_em": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "periodo": {"inicio": inicio, "fim": fim},
        "textos_lidos": len(lidos),
        "fora_por_idioma": {"regra": "texto com mais palavras vazias de inglês ou espanhol do que de português fica fora da CHD, da similitude e das redes",
                            "por_fonte": {f"{f}:{l}": n for (f, l), n in sorted(fora.items())}, "total": sum(fora.values())},
        "grafias_disfarcadas": {"regra": "letra trocada por @, 4, 0, 1, ! ou 3 entre letras (Mounj@ro, tirzep@tida); normalizada só na análise",
                                "textos_por_fonte": dict(collections.Counter(t["fonte"] for t in ts if DISFARCE.search(t["texto"])))},
        "textos": len(ts), "textos_por_fonte": dict(collections.Counter(t["fonte"] for t in ts)),
        "segmentos_total": len(todos), "segmentos_analisados": len(segs),
        "amostra": {"universo_segmentos": len(todos), "analisados": len(segs),
                    "como": "todos os segmentos" if len(segs) == len(todos) else
                    f"amostra aleatória estratificada por fonte, proporcional, semente {SEMENTE}, até {MAX_SEGMENTOS} segmentos",
                    "por_fonte": {f: {"universo": len(por_fonte[f]), "analisados": len(escolha.get(f, []))} for f in por_fonte}},
    })
    try:
        import similitude as sim
        res = sim.ads(X, voc, [s["f"] for s in segs])
        if res:
            col = {f: j for j, f in enumerate(voc)}
            res["segmentos_por_forma"] = {nd["id"]: [int(i) for i in np.nonzero(X[:, col[nd["id"]]])[0]][:400] for nd in res["nos"] if nd["id"] in col}
            resultado["similitude"] = res
            sim.gexf(res, pasta / "similitude.gexf")
    except Exception as erro:
        resultado["similitude"] = {"erro": f"{type(erro).__name__}: {str(erro)[:160]}"}
    comum.gravar(pasta / "segmentos.json", [{"i": s["i"], "f": s["f"], "d": s["d"], "a": s["a"], "u": s["u"], "k": s["k"],
                                             "c": int(rot[s["i"]]), "t": s["t"]} for s in segs])
    comum.gravar(pasta / "chd.json", resultado)
    # redes
    pasta_redes = comum.RAIZ / "data" / "redes"
    pasta_redes.mkdir(parents=True, exist_ok=True)
    nos_p, ar_p, des_p = redes.palavras([sem_disfarce(s["t"]) for s in segs], minimo=10, top=130)
    redes.gexf(nos_p, ar_p, pasta_redes / "palavras.gexf")
    nos_f, ar_f = {}, collections.Counter()
    for t, p in zip(ts, pub):
        fonte_no = f"{t['fonte']}:{p['autor'] or '?'}"
        rotulo = p["autor"] if t["fonte"] in ("imprensa", "checagens") else f"{t['fonte']} {p['autor'] or '(sem autor informado)'}"
        nos_f.setdefault(fonte_no, {"rotulo": rotulo, "tipo": t["fonte"], "n": 0})["n"] += 1
        for termo in t["termos"]:
            if termo:
                nos_f.setdefault(f"termo:{termo}", {"rotulo": termo, "tipo": "termo", "n": 0})["n"] += 1
                ar_f[(fonte_no, f"termo:{termo}")] += 1
    redes.gexf(nos_f, dict(ar_f), pasta_redes / "fontes_termos.gexf")
    # todos os termos e, de cada fonte, as 14 contas ou veículos com mais textos: todas as redes aparecem no desenho
    por_tipo = collections.defaultdict(list)
    for k, v in nos_f.items():
        por_tipo[v["tipo"]].append(k)
    escolhidos = [k for tipo, ks in por_tipo.items()
                  for k in (ks if tipo == "termo" else sorted(ks, key=lambda x: -nos_f[x]["n"])[:14])]
    des_f = redes._desenho(nos_f, ar_f, len(escolhidos), manter=escolhidos)
    if des_f:
        des_f["desenho"] = "todos os termos e, de cada fonte, as 14 contas ou veículos com mais textos; cada nó com as suas 4 ligações mais fortes"
    # para o clique abrir o corpus: índices dos segmentos (da CHD) ligados a cada nó desenhado
    tokens_seg = [set(cr.tokens(sem_disfarce(s["t"]))) for s in segs]
    if des_p:
        for no in des_p["nos"]:
            no["seg"] = [s["i"] for s, tk in zip(segs, tokens_seg) if no["id"] in tk][:400]
    if des_f:
        for no in des_f["nos"]:
            tipo, _, valor = no["id"].partition(":")
            if tipo == "termo":
                no["seg"] = [s["i"] for s in segs if valor in s["k"].split("|")][:400]
            else:
                no["seg"] = [s["i"] for s in segs if s["f"] == tipo and s["a"] == (valor if valor != "?" else "")][:400]
    # rede de hashtags: só hashtag usada em 5 textos ou mais, por 3 autores ou mais (agregado, não identifica pessoa)
    nos_h, ar_h, des_h = hashtags(ts)
    if nos_h:
        redes.gexf(nos_h, ar_h, pasta_redes / "hashtags.gexf")
    if des_h:
        for no in des_h["nos"]:
            marca = "#" + no["id"]
            no["seg"] = [s["i"] for s in segs if marca in s["t"].lower()][:400]
    comum.gravar(pasta_redes / "desenhos.json", {"palavras": des_p, "fontes_termos": des_f, "hashtags": des_h,
                                                 "nota": "Contas de terceiros aparecem como código. Veículos e agências com o nome."})
    comum.gravar(pasta / "volume.json", volume(ts))
    try:
        comum.gravar(comum.RAIZ / "data" / "emojis.json", emojis(segs))
    except Exception as erro:
        print(f"emojis: {type(erro).__name__}: {erro}")
    print(f"gravado data/corpus: {len(ts)} textos, {len(todos)} segmentos, {len(segs)} na CHD, "
          f"{resultado['pct_classificados']}% classificados, {len(resultado['classes'])} classes, {resultado['formas_ativas']} formas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
