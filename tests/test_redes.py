"""Coletor das redes pagas, sem rede e sem gasto: entrada dos atores, leitura dos itens, trava e privacidade."""
import datetime
import json
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import apify  # noqa: E402
import autorizacao  # noqa: E402
import collect_redes as cr  # noqa: E402
import comum  # noqa: E402

INICIO, FIM = datetime.date(2025, 1, 1), datetime.date(2026, 11, 23)
APIFY = {"teto_usd": 10, "autorizacao": "Fulano, 01/01/2030: ok.",
         "etapas": {"teste": 1.0, "publicacoes": 5.0, "comentarios": 2.5, "transcricao": 0.5, "reserva": 1.0}}
CFG = {"ator": "a~b", "preco": {"item": 0.001, "consulta": 0.01}, "itens_teste": 10, "itens_por_termo": 100}


class Entradas(unittest.TestCase):
    def test_entrada_de_cada_rede(self):
        self.assertEqual(cr.entrada("tiktok", "Mounjaro", 10, INICIO), {"keywords": ["Mounjaro"], "maxItems": 10})
        self.assertEqual(cr.entrada("instagram", "caneta do Paraguai", 10, INICIO)["hashtags"], ["canetadoparaguai"])
        x = cr.entrada("x", "caneta do Paraguai", 10, INICIO)["searchTerms"][0]
        self.assertIn('"caneta do Paraguai"', x)
        self.assertIn("since:2025-01-01", x)
        self.assertEqual(cr.entrada("kwai", "Ozempic", 5, INICIO)["postedAfter"], "2025-01-01")

    def test_hashtag_sem_acento(self):
        self.assertEqual(cr.hashtag("Ozempic sem receita"), "ozempicsemreceita")
        self.assertEqual(cr.hashtag("tirzepatida manipulada"), "tirzepatidamanipulada")


class Normalizar(unittest.TestCase):
    def test_tiktok_x_instagram_kwai(self):
        t = cr.normalizar("tiktok", {"id": "1", "authorMeta": {"name": "c"}, "createTimeISO": "2026-03-01T10:00:00.000Z",
                                     "text": "a  b", "playCount": 10, "diggCount": 2, "webVideoUrl": "u"})
        self.assertEqual((t["item_id"], t["conta"], t["publicado_em"], t["texto"], t["visualizacoes"]), ("1", "c", "2026-03-01", "a b", 10))
        x = cr.normalizar("x", {"id": "9", "author": {"userName": "u"}, "createdAt": "Tue Mar 03 10:00:00 +0000 2026",
                                "text": "t", "retweetCount": 1, "quoteCount": 2})
        self.assertEqual((x["publicado_em"], x["compartilhamentos"]), ("2026-03-03", 3))
        i = cr.normalizar("instagram", {"shortCode": "S", "ownerUsername": "o", "timestamp": "2025-05-05T00:00:00Z", "caption": "c", "likesCount": 4})
        self.assertEqual((i["item_id"], i["curtidas"]), ("S", 4))
        k = cr.normalizar("kwai", {"videoId": 7, "uploadTime": 1735689600000, "caption": "k"})
        self.assertEqual((k["item_id"], k["publicado_em"]), ("7", "2025-01-01"))

    def test_descarta_perfil_erro_e_sem_id(self):
        self.assertIsNone(cr.normalizar("kwai", {"type": "profile", "id": 1}))
        self.assertIsNone(cr.normalizar("tiktok", {"error": "x", "id": 1}))
        self.assertIsNone(cr.normalizar("x", {"text": "sem id"}))


def falso(itens_por_termo, custo=0.05):
    chamadas = []
    def executar(ator, entrada, teto):
        chamadas.append((ator, entrada, teto))
        return {"id": f"r{len(chamadas)}", "usageTotalUsd": custo}, itens_por_termo[len(chamadas) - 1]
    return executar, chamadas


class Coletar(unittest.TestCase):
    def test_teste_corta_pelo_periodo_e_junta_termos(self):
        itens = [[{"id": "1", "createTimeISO": "2026-01-01", "authorMeta": {"name": "a"}},
                  {"id": "2", "createTimeISO": "2024-12-31", "authorMeta": {"name": "b"}}],
                 [{"id": "1", "createTimeISO": "2026-01-01", "authorMeta": {"name": "a"}}]]
        executar, chamadas = falso(itens)
        linhas, brutos, resumo, gasto = cr.coletar_rede("tiktok", "teste", ["A", "B"], CFG, APIFY, INICIO, FIM, executar, 0.0)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["termos"], ["A", "B"])
        self.assertEqual(len(brutos), 3)
        self.assertEqual(resumo["por_termo"][0]["no_periodo"], 1)
        self.assertAlmostEqual(gasto, 0.1)
        self.assertTrue(all(teto <= 1.0 for _, _, teto in chamadas))

    def test_custo_minimo_pelo_preco_quando_a_execucao_nao_informa(self):
        executar, _ = falso([[{"id": str(i), "createTimeISO": "2026-01-01"} for i in range(10)]], custo=0)
        _, _, resumo, gasto = cr.coletar_rede("tiktok", "teste", ["A"], CFG, APIFY, INICIO, FIM, executar, 0.0)
        self.assertAlmostEqual(gasto, 0.01 + 0.001 * 10)

    def test_trava_bloqueia_sem_autorizacao(self):
        executar, chamadas = falso([[]])
        with self.assertRaises(autorizacao.GastoNaoAutorizado):
            cr.coletar_rede("tiktok", "teste", ["A"], CFG, {**APIFY, "autorizacao": ""}, INICIO, FIM, executar, 0.0)
        self.assertEqual(chamadas, [])

    def test_publicacoes_reduz_itens_para_caber(self):
        executar, chamadas = falso([[]] * 3)
        _, _, resumo, _ = cr.coletar_rede("tiktok", "publicacoes", ["A", "B", "C"], CFG, APIFY, INICIO, FIM, executar, 4.7)
        self.assertLess(resumo["itens_por_termo"], 100)
        self.assertLessEqual(3 * (0.01 + 0.001 * resumo["itens_por_termo"]), 0.3 + 1e-9)

    def test_erro_de_um_termo_nao_para_os_outros(self):
        def executar(ator, entrada, teto):
            if entrada["keywords"] == ["A"]:
                raise RuntimeError("falhou")
            return {"id": "r", "usageTotalUsd": 0.02}, [{"id": "1", "createTimeISO": "2026-01-01"}]
        linhas, _, resumo, _ = cr.coletar_rede("tiktok", "teste", ["A", "B"], CFG, APIFY, INICIO, FIM, executar, 0.0)
        self.assertEqual(len(linhas), 1)
        self.assertIn("RuntimeError", resumo["por_termo"][0]["erro"])


class Agregado(unittest.TestCase):
    def test_agregado_nao_tem_conta_texto_nem_link(self):
        linhas = [{"rede": "x", "item_id": "1", "conta": "pessoa_comum", "publicado_em": "2026-01-02", "texto": "relato sensível",
                   "visualizacoes": 5, "curtidas": None, "comentarios": 1, "compartilhamentos": 0, "url": "https://x.com/p/1", "termos": ["A"]}]
        ag = cr.agregar("x", linhas, [{"termo": "A", "itens": 1, "lidos": 1, "no_periodo": 1, "no_limite": False, "mais_antigo": "2026-01-02", "erro": None}])
        texto = json.dumps(ag, ensure_ascii=False)
        for proibido in ("pessoa_comum", "relato", "https://"):
            self.assertNotIn(proibido, texto)
        self.assertEqual((ag["publicacoes"], ag["contas_distintas"], ag["curtidas_soma"]), (1, 1, None))


class Configuracao(unittest.TestCase):
    def test_previsto_cabe_nas_etapas(self):
        c = comum.config("coleta")
        n_termos = 15
        previsto = sum(n_termos * (v["preco"].get("consulta", 0) + v["preco"]["item"] * v["itens_por_termo"]) for v in c["pagas"].values())
        teste = sum(len(c["termos_teste"]) * (v["preco"].get("consulta", 0) + v["preco"]["item"] * v["itens_teste"]) for v in c["pagas"].values())
        self.assertLessEqual(previsto, c["apify"]["etapas"]["publicacoes"])
        self.assertLessEqual(teste, c["apify"]["etapas"]["teste"])

    def test_custo_da_execucao(self):
        run = {"chargedEventCounts": {"item": 100}, "pricingInfo": {"pricingPerEvent": {"actorChargeEvents": {"item": {"eventPriceUsd": 0.001}}}}}
        self.assertAlmostEqual(apify.custo(run), 0.1)
        self.assertAlmostEqual(apify.custo({"usageTotalUsd": 0.3}), 0.3)


if __name__ == "__main__":
    unittest.main()
