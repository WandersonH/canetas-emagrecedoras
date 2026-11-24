"""Coletores grátis, sem rede: leitura das respostas, agregação e manifesto."""
import datetime
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import changelog_auto  # noqa: E402
import collect_checagens  # noqa: E402
import collect_imprensa  # noqa: E402
import collect_trends  # noqa: E402
import collect_youtube  # noqa: E402
import rede  # noqa: E402
import sondar_fontes  # noqa: E402

INICIO, FIM = datetime.date(2025, 1, 1), datetime.date(2025, 3, 15)


def video(vid, data, canal="C1", views="10", comentarios="2"):
    return {"id": vid, "snippet": {"publishedAt": f"{data}T12:00:00Z", "channelId": canal, "channelTitle": "x", "title": "t"},
            "statistics": {"viewCount": views, "commentCount": comentarios}}


class YouTube(unittest.TestCase):
    def test_busca_para_no_limite_ou_no_fim(self):
        paginas = [{"pageInfo": {"totalResults": 900}, "items": [{"id": {"videoId": f"v{i}"}} for i in range(50)], "nextPageToken": "p"}]
        resposta = iter(paginas * collect_youtube.MAX_PAGINAS)
        busca = collect_youtube.buscar_termo("k", "Ozempic", INICIO, FIM, leitor=lambda url: next(resposta))
        self.assertEqual(busca["parou_por"], "limite")
        self.assertEqual(busca["universo_estimado"], 900)
        self.assertEqual(busca["paginas"], collect_youtube.MAX_PAGINAS)
        fim = iter([{"pageInfo": {"totalResults": 3}, "items": [{"id": {"videoId": "a"}}, {"id": {"kind": "canal"}}]}])
        busca = collect_youtube.buscar_termo("k", "Saxenda", INICIO, FIM, leitor=lambda url: next(fim))
        self.assertEqual((busca["parou_por"], busca["lido"], busca["ids"]), ("fim_dos_resultados", 1, ["a"]))

    def test_url_de_busca_tem_periodo_e_ordem_por_data(self):
        url = collect_youtube.url_busca("k", "caneta emagrecedora", INICIO, FIM, None)
        self.assertIn("order=date", url)
        self.assertIn("publishedAfter=2025-01-01T00%3A00%3A00Z", url)
        self.assertIn("publishedBefore=2025-03-16T00%3A00%3A00Z", url)

    def test_agregado_so_tem_contagens(self):
        buscas = [{"termo": "Ozempic", "universo_estimado": 100, "lido": 3, "ids": ["a", "b", "b"], "paginas": 1, "parou_por": "fim_dos_resultados"},
                  {"termo": "Wegovy", "universo_estimado": None, "lido": 2, "ids": ["b", "c"], "paginas": 1, "parou_por": "fim_dos_resultados"}]
        videos = [video("a", "2025-01-05"), video("b", "2025-02-01", canal="C2", views="5"), video("c", "2025-02-20", views=None)]
        videos[2]["statistics"] = {}
        ag = collect_youtube.agregar(buscas, videos, INICIO, FIM)
        self.assertEqual(ag["videos_distintos"], 3)
        self.assertEqual(ag["canais_distintos"], 2)
        self.assertEqual(ag["por_mes"], {"2025-01": 1, "2025-02": 2})
        self.assertEqual(ag["visualizacoes_soma"], 15)
        self.assertEqual(ag["videos_em_mais_de_um_termo"], 1)
        self.assertEqual(ag["por_termo"][0]["distintos"], 2)
        texto = json.dumps(ag)
        for proibido in ('"t"', '"x"', "C1", "channelTitle", '"a"'):
            self.assertNotIn(proibido, texto)

    def test_sem_video_nada_vira_zero(self):
        ag = collect_youtube.agregar([], [], INICIO, FIM)
        self.assertIsNone(ag["canais_distintos"])
        self.assertIsNone(ag["visualizacoes_soma"])


class Imprensa(unittest.TestCase):
    def test_meses_cobrem_o_periodo(self):
        fatias = collect_imprensa.meses(datetime.date(2025, 1, 10), datetime.date(2025, 3, 15))
        self.assertEqual(fatias, [(datetime.date(2025, 1, 10), datetime.date(2025, 2, 1)),
                                  (datetime.date(2025, 2, 1), datetime.date(2025, 3, 1)),
                                  (datetime.date(2025, 3, 1), datetime.date(2025, 3, 16))])

    def test_le_o_rss(self):
        rss = b"""<?xml version="1.0"?><rss><channel>
          <item><title>Anvisa aprova nova caneta - Jornal Exemplo</title><link>https://news.google.com/x1</link>
          <pubDate>Wed, 29 Jul 2026 13:00:00 GMT</pubDate><source url="https://jornal.exemplo">Jornal Exemplo</source></item>
          <item><title>Sem fonte</title><link>https://news.google.com/x2</link><pubDate>data ruim</pubDate></item>
        </channel></rss>"""
        itens = collect_imprensa.ler_rss(rss)
        self.assertEqual(itens[0], {"titulo": "Anvisa aprova nova caneta", "veiculo": "Jornal Exemplo",
                                    "site": "https://jornal.exemplo", "data": "2026-07-29", "link": "https://news.google.com/x1"})
        self.assertIsNone(itens[1]["data"])
        self.assertIsNone(itens[1]["veiculo"])

    def test_url_usa_aspas_e_datas(self):
        url = collect_imprensa.url_rss("caneta do Paraguai", datetime.date(2025, 1, 1), datetime.date(2025, 2, 1))
        self.assertIn("%22caneta+do+Paraguai%22", url)
        self.assertIn("after%3A2025-01-01", url)
        self.assertIn("before%3A2025-02-01", url)


class Checagens(unittest.TestCase):
    def test_normaliza_sem_claimant_e_corta_pelo_periodo(self):
        claims = [
            ("Ozempic", {"text": "Alegação A", "claimant": "Pessoa Comum", "claimReview": [
                {"url": "https://agencia.exemplo/a", "publisher": {"name": "Agência", "site": "agencia.exemplo"},
                 "textualRating": "Falso", "title": "Checagem A", "reviewDate": "2025-02-10T00:00:00Z", "languageCode": "pt"}]}),
            ("Mounjaro", {"text": "Alegação A", "claimReview": [{"url": "https://agencia.exemplo/a", "reviewDate": "2025-02-10"}]}),
            ("Wegovy", {"text": "Antiga", "claimReview": [{"url": "https://agencia.exemplo/b", "reviewDate": "2024-12-31"}]}),
        ]
        linhas = collect_checagens.normalizar(claims, INICIO)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["termos"], ["Ozempic", "Mounjaro"])
        self.assertNotIn("Pessoa Comum", json.dumps(linhas))

    def test_busca_pagina_e_para(self):
        respostas = iter([{"claims": [{"text": "a"}], "nextPageToken": "p"}, {"claims": [{"text": "b"}]}])
        itens, parou = collect_checagens.buscar("k", "Ozempic", 30, leitor=lambda url: next(respostas))
        self.assertEqual((len(itens), parou), (2, "fim_dos_resultados"))


class Trends(unittest.TestCase):
    def test_tira_prefixo(self):
        self.assertEqual(collect_trends.sem_prefixo(")]}',\n{\"a\": 1}"), {"a": 1})

    def test_grava_serie_e_uf(self):
        serie = {"default": {"timelineData": [{"time": "1735689600", "formattedTime": "jan", "value": [10, 100], "isPartial": False},
                                              {"time": "1736294400", "formattedTime": "jan", "value": [0, 80], "isPartial": True}]}}
        uf = {"default": {"geoMapData": [{"geoCode": "BR-SP", "geoName": "São Paulo", "value": [40, 60]}]}}
        with tempfile.TemporaryDirectory() as pasta:
            pasta = pathlib.Path(pasta)
            self.assertEqual(collect_trends.gravar_serie(serie, ["Ozempic", "Mounjaro"], pasta / "s.csv"), 2)
            linhas = (pasta / "s.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(linhas[0], "inicio_utc;rotulo;Ozempic;Mounjaro;parcial")
            self.assertEqual(linhas[1], "2025-01-01;jan;10;100;0")
            self.assertTrue(linhas[2].endswith(";1"))
            self.assertEqual(collect_trends.gravar_uf(uf, ["Ozempic", "Mounjaro"], pasta / "u.csv"), 1)

    def test_grupos_tem_no_maximo_cinco_termos(self):
        import comum
        for grupo in comum.config("trends")["grupos"]:
            self.assertLessEqual(len(grupo["termos"]), 5, grupo["nome"])


class Manifesto(unittest.TestCase):
    def test_formato_que_o_estado_le_e_sem_chave(self):
        with tempfile.TemporaryDirectory() as pasta, unittest.mock.patch.dict("os.environ", {"YOUTUBE_API_KEY": "SEGREDO123"}):
            raiz = pathlib.Path(pasta)
            m = rede.Manifesto("youtube", {"termos": ["Ozempic"]}, "99")
            m.bloqueio("falhou em https://x?key=SEGREDO123")
            caminho = m.gravar(raiz)
            dado = json.loads(caminho.read_text(encoding="utf-8"))
        for campo in ("frente", "etapa", "run_id", "universo", "lido", "amostra", "parou_por", "custo_usd", "arquivos"):
            self.assertIn(campo, dado)
        self.assertEqual(dado["custo_usd"], 0)
        self.assertNotIn("SEGREDO123", json.dumps(dado))

    def test_periodo_lido_e_termos_da_configuracao(self):
        inicio, fim = rede.periodo_lido(hoje=datetime.date(2030, 1, 1))
        self.assertEqual(inicio, datetime.date(2025, 1, 1))
        self.assertGreaterEqual(fim, inicio)
        termos = rede.termos_de_busca()
        self.assertTrue(termos)
        self.assertNotIn("TG", [t["termo"] for t in termos])


class Sondagem(unittest.TestCase):
    INDICE = """<html><body><h1>Index of /dados/SNGPC/Industrializados</h1><pre>
<a href="?C=N;O=D">Name</a> <a href="?C=M;O=A">Last modified</a>
<a href="/dados/SNGPC/">Parent Directory</a>
<a href="EDA_Industrializados_202104.csv">EDA_Industrializados_202104.csv</a>   2021-05-10 08:12  1.2G
<a href="EDA_Industrializados_202512.csv">EDA_Industrializados_202512.csv</a>   2026-01-15 09:00  980M
<a href="antigos/">antigos/</a>                 2024-01-01 10:00    -
</pre></body></html>"""

    def test_le_indice_e_meses(self):
        itens = sondar_fontes.ler_indice(self.INDICE, "https://dados.exemplo/dados/SNGPC/Industrializados/")
        self.assertEqual([i["nome"] for i in itens], ["EDA_Industrializados_202104.csv", "EDA_Industrializados_202512.csv", "antigos/"])
        self.assertEqual(itens[0]["tamanho"], "1.2G")
        self.assertEqual(itens[1]["data"], "2026-01-15 09:00")
        self.assertTrue(itens[2]["pasta"])
        self.assertEqual(sondar_fontes.meses_publicados(itens), {"quantidade": 2, "primeiro": "202104", "ultimo": "202512", "lista": ["202104", "202512"]})
        self.assertEqual(sondar_fontes.meses_publicados([]), {"quantidade": None, "primeiro": None, "ultimo": None, "lista": []})

    def test_le_indice_com_endereco_absoluto(self):
        pagina = '<a href="/dados/">Diretório pai</a><a href="/dados/VigiMed_Notificacoes.csv">VigiMed_Notificacoes.csv</a> 2026-11-01 03:00 2.1G<a href="/outra/x.csv">x.csv</a><a href="/dados/SNGPC/">SNGPC/</a>'
        itens = sondar_fontes.ler_indice(pagina, "https://dados.exemplo/dados/")
        self.assertEqual([i["nome"] for i in itens], ["VigiMed_Notificacoes.csv", "SNGPC/"])
        self.assertEqual(itens[0]["url"], "https://dados.exemplo/dados/VigiMed_Notificacoes.csv")

    def test_le_pagina_e_ignora_links_comuns(self):
        pagina = '<a href="/arquivos/lista_pmc_202611.xlsx">Lista PMC</a><a href="/sobre">Sobre</a><a href="/arquivos/lista_pmc_202611.xlsx">repetido</a>'
        itens = sondar_fontes.ler_pagina(pagina, "https://www.gov.br/anvisa/precos")
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["url"], "https://www.gov.br/arquivos/lista_pmc_202611.xlsx")

    def test_fonte_fora_do_ar_nao_vira_zero(self):
        fonte = sondar_fontes.FONTES[1]
        r = sondar_fontes.sondar(fonte, leitor=lambda url: {"http": None, "tipo": None, "corpo": b"", "erro": "URLError: x"})
        self.assertIsNone(r["arquivos"])
        self.assertIsNone(r["meses"]["quantidade"])
        self.assertEqual(sondar_fontes.resumo({"fontes": [r]}), [f"{fonte['id']}: sem acesso (URLError: x)"])


class Changelog(unittest.TestCase):
    PARTES = {"mudou": ["a"], "porque": ["b"], "executado": ["c"], "pendente": ["d"], "evidencia": ["e"]}

    def test_entrada_entra_acima_das_outras(self):
        atual = "# CHANGELOG\n\nTexto.\n\n## 01/01/2026 · Antiga\n\nx\n"
        novo = changelog_auto.inserir(atual, changelog_auto.entrada("Nova", "02/01/2026", self.PARTES))
        self.assertLess(novo.index("## 02/01/2026 · Nova"), novo.index("## 01/01/2026 · Antiga"))
        for rotulo in ("O que mudou", "Por quê", "O que foi executado de verdade", "O que ficou pendente", "Onde está a evidência"):
            self.assertIn(f"**{rotulo}**", novo)

    def test_secao_vazia_e_recusada(self):
        with self.assertRaises(ValueError):
            changelog_auto.entrada("X", "01/01/2026", {**self.PARTES, "pendente": ["  "]})


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()


class YouTubeHistorico(unittest.TestCase):
    def test_meses_do_mais_recente_ao_mais_antigo(self):
        import collect_youtube_historico as h
        m = h.meses(datetime.date(2025, 1, 10), datetime.date(2025, 3, 5))
        self.assertEqual([x[0] for x in m], ["2025-03", "2025-02", "2025-01"])
        self.assertEqual(m[0][1:], (datetime.date(2025, 3, 1), datetime.date(2025, 3, 5)))
        self.assertEqual(m[2][1], datetime.date(2025, 1, 10))
        self.assertEqual(m[1][2], datetime.date(2025, 2, 28))

    def test_cota_esgotada_interrompe(self):
        import io
        import urllib.error
        import collect_youtube_historico as h
        def leitor(url):
            raise urllib.error.HTTPError(url, 403, "x", {}, io.BytesIO(b'{"error":{"errors":[{"reason":"quotaExceeded"}]}}'))
        with self.assertRaises(h.CotaEsgotada):
            h.buscar_mes("k", "Ozempic", INICIO, FIM, 1, leitor=leitor)

    def test_uma_pagina_marca_limite(self):
        import collect_youtube_historico as h
        r = h.buscar_mes("k", "Ozempic", INICIO, FIM, 1, leitor=lambda url: {"pageInfo": {"totalResults": 800}, "items": [{"id": {"videoId": "a"}}], "nextPageToken": "p"})
        self.assertEqual((r["estimativa"], r["ids"], r["no_limite"]), (800, ["a"], True))


class Corpus(unittest.TestCase):
    def test_idioma(self):
        import build_corpus as bc
        self.assertEqual(bc.idioma("Como tomar Ozempic sem efeito colateral e o que fazer"), "pt")
        self.assertEqual(bc.idioma("What to know about Ozempic and weight loss in your body"), "en")
        self.assertEqual(bc.idioma("Cómo es el tratamiento con la semaglutida para la obesidad"), "es")
        self.assertEqual(bc.idioma("Mounjaro Ozempic"), "pt")

    def test_publico_anonimiza_terceiros_e_mantem_imprensa(self):
        import build_corpus as bc
        cod = {"perfil_x": "A0001"}
        t = {"fonte": "tiktok", "texto": "perdi 10kg @amiga www.loja.com", "autor": "Perfil_X", "url": None, "veiculo": None}
        p = bc.publico(t, cod)
        self.assertEqual((p["autor"], p["url"]), ("A0001", None))
        self.assertNotRegex(p["texto"], r"\\d|@|loja")
        n = bc.publico({"fonte": "imprensa", "texto": "Anvisa aprova 5 canetas", "autor": "G1", "url": "https://g1", "veiculo": "G1"}, cod)
        self.assertEqual((n["texto"], n["autor"], n["url"]), ("Anvisa aprova 5 canetas", "G1", "https://g1"))

    def test_grafia_disfarcada(self):
        import build_corpus as bc
        self.assertEqual(bc.sem_disfarce("Mounj@ro e tirzep@tida, 0zempic, Ozemp1c"), "Mounjaro e tirzepatida, 0zempic, Ozempic")
        self.assertEqual(bc.sem_disfarce("GLP-1 e 15 mg"), "GLP-1 e 15 mg")

    def test_amostra_estratificada(self):
        import random
        import build_corpus as bc
        a = bc.amostra_estratificada({"youtube": 800, "imprensa": 200}, 100, random.Random(1))
        self.assertEqual((len(a["youtube"]), len(a["imprensa"])), (80, 20))
        self.assertEqual(bc.amostra_estratificada({"x": 5}, 100, random.Random(1)), {"x": [0, 1, 2, 3, 4]})


class YouTubeHistoricoRetomada(unittest.TestCase):
    def test_recupera_estado_do_bruto(self):
        import collect_youtube_historico as h
        with tempfile.TemporaryDirectory() as pasta:
            pasta = pathlib.Path(pasta)
            (pasta / "bruto" / "youtube_historico" / "X").mkdir(parents=True)
            (pasta / "bruto" / "youtube_historico" / "X" / "0000.json").write_text(json.dumps(
                {"termo": "Ozempic", "mes": "2025-03", "paginas": [{"pageInfo": {"totalResults": 90}, "items": [{"id": {"videoId": "v1"}}], "nextPageToken": "p"}]}), encoding="utf-8")
            estado = {"feitos": {}}
            self.assertEqual(h.recuperar_do_bruto(pasta, estado), 1)
            self.assertEqual(estado["feitos"]["Ozempic|2025-03"]["ids"], ["v1"])
            self.assertTrue(estado["feitos"]["Ozempic|2025-03"]["no_limite"])
            self.assertEqual(h.recuperar_do_bruto(pasta, estado), 0)
