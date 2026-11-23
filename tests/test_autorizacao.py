"""Coleta paga só roda com teto maior que zero e frase de autorização gravados."""
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import autorizacao  # noqa: E402
import comum  # noqa: E402

LIBERADO = {
    "teto_usd": 10,
    "autorizacao": "Fulano, 01/01/2030 (chat): autorizo US$ 10 para a coleta de teste.",
    "etapas": {"teste": 1, "publicacoes": 4, "comentarios": 3, "terceiros": 1, "reserva": 1},
}


class Trava(unittest.TestCase):
    def test_configuracao_atual_do_repositorio_bloqueia(self):
        apify = comum.config("coleta")["apify"]
        if float(apify["teto_usd"]) > 0:
            self.skipTest("há teto autorizado; a trava é conferida pelos casos sintéticos")
        with self.assertRaises(autorizacao.GastoNaoAutorizado):
            autorizacao.verificar(apify, "teste", 0.01)
        self.assertEqual(autorizacao.main(["--etapa", "teste", "--previsto", "0.01"]), 1)

    def test_teto_zero_bloqueia(self):
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "teto total"):
            autorizacao.verificar({**LIBERADO, "teto_usd": 0}, "teste", 0.5)

    def test_sem_frase_bloqueia(self):
        for frase in ("", "   ", None):
            with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "autorização"):
                autorizacao.verificar({**LIBERADO, "autorizacao": frase}, "teste", 0.5)

    def test_etapa_desconhecida_ou_sem_teto_bloqueia(self):
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "desconhecida"):
            autorizacao.verificar(LIBERADO, "inexistente", 0.5)
        sem_teto = {**LIBERADO, "etapas": {**LIBERADO["etapas"], "teste": 0}}
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "teto da etapa"):
            autorizacao.verificar(sem_teto, "teste", 0.5)

    def test_soma_das_etapas_acima_do_total_bloqueia(self):
        estourado = {**LIBERADO, "etapas": {**LIBERADO["etapas"], "reserva": 5}}
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "soma"):
            autorizacao.verificar(estourado, "teste", 0.5)

    def test_gasto_feito_mais_previsto_acima_da_etapa_bloqueia(self):
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "passaria do teto"):
            autorizacao.verificar(LIBERADO, "teste", 0.6, ja_gasto_usd=0.5)

    def test_dentro_do_teto_devolve_a_sobra(self):
        self.assertAlmostEqual(autorizacao.verificar(LIBERADO, "teste", 0.4, ja_gasto_usd=0.5), 0.1)
        self.assertAlmostEqual(autorizacao.verificar(LIBERADO, "teste", 1.0), 0.0)

    def test_gasto_negativo_bloqueia(self):
        with self.assertRaisesRegex(autorizacao.GastoNaoAutorizado, "negativo"):
            autorizacao.verificar(LIBERADO, "teste", -1)

    def test_gasto_da_etapa_soma_so_os_manifestos_dela(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = pathlib.Path(pasta)
            for nome, etapa, custo in (("a", "teste", 0.25), ("b", "teste", 0.5), ("c", "comentarios", 2), ("d", "teste", None)):
                (pasta / f"{nome}.json").write_text(json.dumps({"etapa": etapa, "custo_usd": custo}), encoding="utf-8")
            self.assertAlmostEqual(autorizacao.gasto_da_etapa("teste", pasta), 0.75)
            self.assertAlmostEqual(autorizacao.gasto_da_etapa("publicacoes", pasta), 0.0)
        self.assertEqual(autorizacao.gasto_da_etapa("teste", pathlib.Path("/caminho/que/nao/existe")), 0.0)


if __name__ == "__main__":
    unittest.main()
