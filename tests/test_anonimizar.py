"""Texto de terceiros só vai ao público depois de anonimizado."""
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import anonimizar  # noqa: E402


class Texto(unittest.TestCase):
    def test_numero_de_saude_some(self):
        saida = anonimizar.anonimizar_texto("Perdi 12kg em 3 meses tomando 2,5 mg, tenho 34 anos e pesava 98,4 kg")
        self.assertNotRegex(saida, r"\d")
        self.assertIn("[n]kg", saida)
        self.assertIn("[n] mg", saida)

    def test_preco_e_data_somem(self):
        saida = anonimizar.anonimizar_texto("Paguei R$ 1.200,00 no dia 05/03/2026 às 14:30")
        self.assertNotRegex(saida, r"\d")

    def test_perfil_vira_marca(self):
        saida = anonimizar.anonimizar_texto("olha isso @perfil.ficticio_01 e @outro_ficticio")
        self.assertEqual(saida, "olha isso [perfil] e [perfil]")

    def test_link_some_inclusive_sem_protocolo(self):
        for texto in ("compre em https://loja.exemplo.com/caneta?x=1 agora", "chama no www.exemplo.com.br/promo",
                      "site exemplo-ficticio.shop tem", "link wa.me/5500900000000 aqui"):
            with self.subTest(texto=texto):
                saida = anonimizar.anonimizar_texto(texto)
                self.assertIn("[link]", saida)
                self.assertNotIn("exemplo", saida)
                self.assertNotIn("ficticio", saida)
                self.assertNotIn("wa.me", saida)

    def test_telefone_some(self):
        for texto in ("me chama (00) 90000-0000", "zap 00 900000000", "+55 00 90000-0000", "liga 90000-0000", "fixo (00) 3000-0000"):
            with self.subTest(texto=texto):
                saida = anonimizar.anonimizar_texto(texto)
                self.assertIn("[telefone]", saida)
                self.assertNotRegex(saida, r"\d")

    def test_email_some(self):
        saida = anonimizar.anonimizar_texto("manda para fulana.tal+x@exemplo.com.br por favor")
        self.assertEqual(saida, "manda para [e-mail] por favor")

    def test_nome_de_produto_com_numero_fica(self):
        saida = anonimizar.anonimizar_texto("agonista de GLP-1 e a tal T36, 15 mg")
        self.assertIn("GLP-1", saida)
        self.assertIn("T36", saida)
        self.assertIn("[n] mg", saida)
        self.assertEqual(anonimizar.tem_resto_identificavel(saida), [])

    def test_texto_vazio(self):
        self.assertEqual(anonimizar.anonimizar_texto(""), "")
        self.assertEqual(anonimizar.anonimizar_texto(None), "")

    def test_texto_sem_dado_fica_igual(self):
        texto = "Comecei o tratamento com acompanhamento médico e senti enjoo na primeira semana."
        self.assertEqual(anonimizar.anonimizar_texto(texto), texto)

    def test_resto_identificavel_e_acusado(self):
        self.assertEqual(anonimizar.tem_resto_identificavel("perdi 12 kg"), ["número"])
        self.assertIn("perfil", anonimizar.tem_resto_identificavel("fala com @perfil_ficticio"))
        self.assertIn("link", anonimizar.tem_resto_identificavel("veja https://exemplo.com"))

    def test_saida_nunca_tem_resto(self):
        casos = [
            "Tomo Mounjaro 5mg desde 10/01/2026, perdi 8,5kg. @perfil.ficticio me indicou, zap (00) 90000-0000",
            "Comprei por R$900 no site exemplo-ficticio.store, entrega em 2 dias, contato fulano@exemplo.com",
            "IMC 31.2, 1m68, 87kg -> 79kg em 60 dias",
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                self.assertEqual(anonimizar.tem_resto_identificavel(anonimizar.anonimizar_texto(texto)), [])


class Autores(unittest.TestCase):
    def test_codigo_na_ordem_de_aparicao_e_estavel(self):
        tabela = anonimizar.codigos_de_autores(["Ana", "bia", "ANA ", "", None, "Caio"])
        self.assertEqual(tabela, {"ana": "A0001", "bia": "A0002", "caio": "A0003"})

    def test_codigo_nao_carrega_o_nome(self):
        tabela = anonimizar.codigos_de_autores(["usuario_muito_especifico"])
        self.assertNotIn("usuario", "".join(tabela.values()))


if __name__ == "__main__":
    unittest.main()
