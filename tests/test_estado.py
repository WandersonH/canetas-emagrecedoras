"""O resumo que a página lê: ausente é null, cobertura completa só pela data inicial, custo nunca aparece."""
import json
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import build_estado  # noqa: E402
import comum  # noqa: E402

COLETA = {
    "gratuitas": {"youtube": {"nome": "YouTube", "via": "API"}},
    "pagas": {"tiktok": {"nome": "TikTok", "via": "Apify"}},
}


def manifesto(**campos):
    base = {"frente": "youtube", "etapa": "gratis", "run_id": "run-1", "terminado_em": "2030-01-01T10:00:00Z",
            "universo": {"valor": 1000, "fonte": "total informado pela plataforma"}, "lido": 400,
            "amostra": {"n": 400, "como": "todos os itens lidos"}, "parou_por": "data_inicial", "custo_usd": 0}
    return {**base, **campos}


class Estado(unittest.TestCase):
    def test_sem_manifesto_tudo_ausente_e_nunca_zero(self):
        estado = build_estado.montar(COLETA, [])
        self.assertIsNone(estado["manifestos_lidos"])
        self.assertEqual([f["id"] for f in estado["frentes"]], ["youtube", "tiktok"])
        for frente in estado["frentes"]:
            for campo in ("coletas", "universo", "lido", "amostra", "cobertura", "ultima_coleta"):
                self.assertIsNone(frente[campo], f"{frente['id']}.{campo}")

    def test_frente_gratis_e_paga(self):
        estado = build_estado.montar(COLETA, [])
        self.assertEqual({f["id"]: f["paga"] for f in estado["frentes"]}, {"youtube": False, "tiktok": True})

    def test_cobertura_completa_so_pela_data_inicial(self):
        self.assertEqual(build_estado.cobertura(manifesto(parou_por="data_inicial")), "completa")
        for motivo in ("limite", "fim_dos_resultados", None, ""):
            self.assertEqual(build_estado.cobertura(manifesto(parou_por=motivo)), "parcial")

    def test_universo_que_a_plataforma_nao_informa_fica_ausente(self):
        estado = build_estado.montar(COLETA, [manifesto(universo={"valor": None, "fonte": None})])
        youtube = estado["frentes"][0]
        self.assertIsNone(youtube["universo"])
        self.assertEqual(youtube["lido"], 400)

    def test_zero_lido_e_zero_e_nao_ausente(self):
        estado = build_estado.montar(COLETA, [manifesto(lido=0, amostra={"n": 0, "como": "nenhum item no período"})])
        self.assertEqual(estado["frentes"][0]["lido"], 0)
        self.assertEqual(estado["frentes"][0]["amostra"], 0)

    def test_usa_a_coleta_mais_recente_e_guarda_os_runs(self):
        antigo = manifesto(run_id="run-1", terminado_em="2030-01-01T10:00:00Z", lido=100)
        novo = manifesto(run_id="run-2", terminado_em="2030-02-01T10:00:00Z", lido=900, parou_por="limite")
        youtube = build_estado.montar(COLETA, [novo, antigo])["frentes"][0]
        self.assertEqual(youtube["lido"], 900)
        self.assertEqual(youtube["cobertura"], "parcial")
        self.assertEqual(youtube["coletas"], 2)
        self.assertEqual(youtube["runs"], ["run-1", "run-2"])

    def test_custo_nunca_entra_no_estado(self):
        estado = build_estado.montar(COLETA, [manifesto(frente="tiktok", etapa="teste", custo_usd=0.37)])
        texto = json.dumps(estado, ensure_ascii=False)
        self.assertNotIn("custo", texto)
        self.assertNotIn("0.37", texto)
        self.assertNotIn("usd", texto.lower())

    def test_estado_do_repositorio_esta_em_dia(self):
        caminho = RAIZ / "data" / "estado.json"
        self.assertTrue(caminho.exists(), "rode: python scripts/build_estado.py")
        esperado = build_estado.montar(comum.config("coleta"), build_estado.ler_manifestos())
        self.assertEqual(comum.carregar(caminho), esperado, "data/estado.json desatualizado: rode scripts/build_estado.py")


if __name__ == "__main__":
    unittest.main()
