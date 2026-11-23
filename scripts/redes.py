"""Redes para o Gephi: desenho na página (comunidades e posições) e exportação em GEXF.

- gexf(): arquivo GEXF com tipo, peso e comunidade de cada nó (Clauset-Newman-Moore, o agrupamento padrão do NodeXL).
  No Gephi, ForceAtlas 2 para ver comunidades e Modularity (Louvain) para os grupos; scripts/estatisticas_redes.py
  calcula as mesmas medidas, com Louvain e o índice E-I.
- _desenho(): os nós de maior peso, com comunidades e posições por componente, para a página.
- palavras(): coocorrência de palavras no mesmo texto.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import chd_reinert as cr

MIN_PUBLICO = 10000


def _layout(G, peso="weight") -> dict:
    """Comunidades por modularidade; posições por componente (cada componente ganha uma área própria, em grade,
    proporcional ao tamanho) — o spring_layout do grafo inteiro joga componentes pequenos para os cantos."""
    import math
    import networkx as nx
    com = {n: i for i, c in enumerate(nx.community.greedy_modularity_communities(G, weight=peso)) for n in c} if G.number_of_edges() else {}
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    pos, x0, y0, linha_h, largura = {}, 0.0, 0.0, 0.0, 4.0
    for comp in comps:
        H = G.subgraph(comp)
        lado = max(0.35, math.sqrt(len(comp)) / math.sqrt(max(1, len(comps[0]))) * 2.0)
        p = nx.spring_layout(H, seed=7, weight=peso, k=1.2 / math.sqrt(max(1, len(comp)))) if len(comp) > 1 else {next(iter(comp)): (0.0, 0.0)}
        if x0 + lado > largura:
            x0, y0, linha_h = 0.0, y0 + linha_h + 0.15, 0.0
        for n, (x, y) in p.items():
            pos[n] = (x0 + (x + 1) / 2 * lado, y0 + (y + 1) / 2 * lado)
        x0 += lado + 0.15
        linha_h = max(linha_h, lado)
    return com, pos


def gexf(nos: dict, arestas: dict, caminho: Path, dirigida: bool = False) -> None:
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")  # noqa: E731
    # 02/11/2026: comunidade por Clauset-Newman-Moore (networkx.greedy_modularity_communities), o agrupamento padrão do NodeXL
    # (Groups › Group by Cluster), para que a exportação ao NodeXL traga os mesmos grupos
    com = {}
    try:
        import networkx as nx
        H = nx.Graph()
        H.add_nodes_from(nos)
        for (a, b), w in arestas.items():
            if a != b and a in nos and b in nos:
                H.add_edge(a, b, weight=(H[a][b]["weight"] + w) if H.has_edge(a, b) else w)
        if H.number_of_edges():
            com = {n: f"G{i + 1}" for i, c in enumerate(nx.community.greedy_modularity_communities(H, weight="weight")) for n in c}
    except Exception:  # noqa: BLE001
        com = {}
    l = ['<?xml version="1.0" encoding="UTF-8"?>', '<gexf xmlns="http://gexf.net/1.3" version="1.3">',
         f'<graph defaultedgetype="{"directed" if dirigida else "undirected"}">',
         '<attributes class="node"><attribute id="0" title="tipo" type="string"/><attribute id="1" title="peso" type="double"/>'
         '<attribute id="2" title="comunidade" type="string"/></attributes>', "<nodes>"]
    for k, v in nos.items():
        l.append(f'<node id="{esc(k)}" label="{esc(v.get("rotulo", k))}"><attvalues><attvalue for="0" value="{esc(v.get("tipo", ""))}"/>'
                 f'<attvalue for="1" value="{v.get("n", 0)}"/><attvalue for="2" value="{esc(com.get(k, "sem ligação"))}"/></attvalues></node>')
    l.append("</nodes><edges>")
    for i, ((a, b), w) in enumerate(arestas.items()):
        l.append(f'<edge id="{i}" source="{esc(a)}" target="{esc(b)}" weight="{w}"/>')
    l += ["</edges>", "</graph>", "</gexf>"]
    caminho.write_text("\n".join(l), encoding="utf-8")


def _desenho(nos: dict, arestas: dict, top: int = 90) -> dict | None:
    import networkx as nx
    G = nx.Graph()
    for (a, b), w in arestas.items():
        G.add_edge(a, b, weight=w)
    if not G.number_of_nodes():
        return None
    manter = sorted(G.nodes, key=lambda k: -(nos.get(k, {}).get("n") or 0))[:top]
    H = G.subgraph(manter).copy()
    H.remove_nodes_from([n for n in list(H.nodes) if H.degree(n) == 0])
    if not H.number_of_nodes():
        return None
    com, pos = _layout(H)
    return {"nos": [{"id": n, "rotulo": nos.get(n, {}).get("rotulo", n), "tipo": nos.get(n, {}).get("tipo", ""), "n": nos.get(n, {}).get("n") or 0,
                     "grupo": com.get(n, 0), "x": round(float(pos[n][0]), 4), "y": round(float(pos[n][1]), 4)} for n in H.nodes],
            "arestas": [[a, b, d["weight"]] for a, b, d in H.edges(data=True)][:700],
            "total_nos": len(nos), "total_arestas": len(arestas), "comunidades": len(set(com.values())) if com else 0}



def palavras(textos: list[str], minimo: int = 5, top: int = 80) -> tuple[dict, dict, dict | None]:
    docs = [set(cr.tokens(t)) for t in textos]
    df = Counter(t for d in docs for t in d)
    voc = {t for t, n in df.items() if n >= minimo}
    ar = Counter()
    for d in docs:
        ws = sorted(d & voc)
        for i, a in enumerate(ws):
            for b in ws[i + 1:]:
                ar[(a, b)] += 1
    ar = Counter({k: w for k, w in ar.items() if w >= 3})
    nos = {t: {"rotulo": t, "tipo": "palavra", "n": df[t]} for t in voc}
    return nos, dict(ar), _desenho(nos, ar, top)
