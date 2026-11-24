"""Checagens das agências pelo Google Notícias, com RSS de exemplo (sem rede)."""
import datetime
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import collect_checagens_agencias as agencias  # noqa: E402

RSS = b"""<rss><channel>
<item><title>Checagem sobre caneta - Aos Fatos</title><link>https://news.google.com/a1</link>
<pubDate>Mon, 10 Mar 2025 10:00:00 GMT</pubDate><source url="https://www.aosfatos.org">Aos Fatos</source></item>
<item><title>Antiga - Aos Fatos</title><link>https://news.google.com/a0</link>
<pubDate>Mon, 10 Mar 2024 10:00:00 GMT</pubDate><source url="https://www.aosfatos.org">Aos Fatos</source></item>
</channel></rss>"""


class Agencias(unittest.TestCase):
    def test_consulta_tem_restricao_e_periodo(self):
        q = agencias.consulta("site:aosfatos.org", ["Ozempic", "caneta emagrecedora"],
                              datetime.date(2025, 1, 1), datetime.date(2026, 11, 24))
        self.assertIn('(Ozempic OR "caneta emagrecedora")', q)
        self.assertIn("site:aosfatos.org", q)
        self.assertIn("after:2025-01-01", q)

    def test_coletar_descarta_fora_do_periodo_e_junta_grupos(self):
        consultas, checagens = agencias.coletar(datetime.date(2025, 1, 1), datetime.date(2026, 11, 23),
                                                leitor=lambda url: RSS, pausa=0)
        self.assertEqual(len(consultas), len(agencias.AGENCIAS) * len(agencias.GRUPOS))
        self.assertEqual([c["link"] for c in checagens], ["https://news.google.com/a1"])
        self.assertEqual(sorted(checagens[0]["grupos"]), sorted(agencias.GRUPOS))

    def test_erro_fica_registrado_sem_zero(self):
        def falha(url):
            raise TimeoutError("tempo")
        consultas, checagens = agencias.coletar(datetime.date(2025, 1, 1), datetime.date(2026, 11, 23), leitor=falha, pausa=0)
        self.assertTrue(all(c["lidos"] is None and c["erro"] for c in consultas))
        self.assertEqual(checagens, [])


if __name__ == "__main__":
    unittest.main()
