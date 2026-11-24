"""Agregados da codificação manual JAMA."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import comum  # noqa: E402
import resumo_jama  # noqa: E402


def linha(url, perfil, caneta, a, b, c, d):
    return {"URL": url, "Tipo de perfil": perfil, "Tipo de caneta": caneta, "Data": "2025-01-02", "ID do vídeo": None,
            "Autoria (0/1)": a, "Atribuição (0/1)": b, "Disclosure (0/1)": c, "Atualidade (0/1)": d,
            "JAMA Score (0–4)": a + b + c + d, "Tipo de conteúdo": "x"}


class Jama(unittest.TestCase):
    def setUp(self):
        self.cfg = comum.config("jama")

    def test_endereco_repetido_conta_uma_vez_e_percentual(self):
        rs = [linha("https://www.tiktok.com/@a/video/111111111111111111", "Médico", "Mounjaro", 1, 0, 0, 1),
              linha("https://www.tiktok.com/@a/video/111111111111111111", "Médico", "Mounjaro", 1, 0, 0, 1),
              linha("https://www.tiktok.com/@b/video/222222222222222222", "Influenciador", "Wegovy", 0, 0, 1, 1)]
        r = resumo_jama.resumir(rs, self.cfg, {"222222222222222222"})
        self.assertEqual((r["linhas_na_planilha"], r["videos"], r["linhas_repetidas"]), (3, 2, 1))
        crit = {c["id"]: c for c in r["criterios"]}
        self.assertEqual(crit["autoria"]["pct"], 50.0)
        self.assertEqual(crit["atualidade"]["presente"], 2)
        self.assertEqual(r["pontuacao"]["distribuicao"]["2"], 2)
        self.assertEqual(r["pontuacao"]["soma_confere"], 2)
        self.assertEqual(r["na_coleta_do_projeto"], 1)
        grupos = {g["grupo"] for g in r["por_tipo_de_caneta"]}
        self.assertEqual(grupos, {"tirzepatida", "semaglutida"})

    def test_rotulo_desconhecido_nao_some(self):
        self.assertEqual(resumo_jama.grupo("Astronauta", self.cfg["tipo_de_perfil"]["grupos"]), "outro rótulo")
        self.assertEqual(resumo_jama.grupo(None, self.cfg["tipo_de_perfil"]["grupos"]), "sem rótulo")

    def test_ponto_ausente_nao_vira_zero(self):
        self.assertIsNone(resumo_jama.ponto(None))
        self.assertIsNone(resumo_jama.ponto("—"))


if __name__ == "__main__":
    unittest.main()
