"""Triagem de venda irregular: tipos, homônimos e nenhum número ou link nos sinais."""
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import venda_irregular as vi  # noqa: E402


class Venda(unittest.TestCase):
    def setUp(self):
        self.rs = vi.regras(RAIZ)

    def c(self, texto):
        return vi.classificar(texto, self.rs)

    def test_oferta_sem_receita_e_paraguai(self):
        r = self.c("Vendo caneta do Paraguai sem receita, chama no whats (11) 91234-5678, envio para todo Brasil")
        self.assertIn("oferta sem receita", r["tipos"])
        self.assertIn("produto sem registro", r["tipos"])
        self.assertIn("telefone", r["sinais"]["oferta"])
        juntos = " ".join(x for v in r["sinais"].values() for x in v)
        self.assertNotRegex(juntos, r"\\d{4}")

    def test_link_vira_rotulo(self):
        r = self.c("tirzepatida manipulada pronta entrega https://exemplo.invalido/loja")
        self.assertIn("manipulado", r["tipos"])
        self.assertIn("link", r["sinais"]["oferta"])

    def test_sem_sinal_de_venda_nao_e_oferta(self):
        r = self.c("Usar caneta do Paraguai sem receita é perigoso, diz médico")
        self.assertFalse(r["oferta"])
        self.assertEqual(r["tipos"], [])

    def test_homonimo_sem_tema_nao_conta(self):
        r = self.c("vendo TG pix")
        self.assertNotIn("produto sem registro", r["tipos"])
        r = self.c("vendo TG caneta pix")
        self.assertIn("produto sem registro", r["tipos"])

    def test_golpe_e_mencao(self):
        r = self.c("Cuidado, caí no golpe da caneta falsa")
        self.assertEqual(r["tipos"], ["menção a golpe ou falsificação"])


if __name__ == "__main__":
    unittest.main()
