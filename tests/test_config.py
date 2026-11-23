"""A configuração tem de ser coerente com as regras do projeto."""
import datetime
import pathlib
import re
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import comum  # noqa: E402

DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
NOME_DE_SEGREDO = re.compile(r"^[A-Z][A-Z0-9_]+$")


def data(texto):
    return datetime.datetime.strptime(texto, "%d/%m/%Y").date()


class Projeto(unittest.TestCase):
    def setUp(self):
        self.projeto = comum.config("projeto")

    def test_marcos_candidatos_tem_data_fonte_e_endereco(self):
        for candidato in self.projeto["marco"]["candidatos"]:
            with self.subTest(candidato=candidato["descricao"]):
                self.assertRegex(candidato["data"], DATA)
                data(candidato["data"])
                self.assertTrue(candidato["fonte"].strip())
                self.assertTrue(candidato["url"].startswith("https://"))
                self.assertTrue(candidato["situacao"].strip())

    def test_marcos_em_ordem_de_data(self):
        datas = [data(c["data"]) for c in self.projeto["marco"]["candidatos"]]
        self.assertEqual(datas, sorted(datas))

    def test_janela_definida_e_valida_ou_ausente(self):
        for nome in ("base", "nucleo"):
            janela = self.projeto["janelas"][nome]
            inicio, fim = janela["inicio"], janela["fim"]
            with self.subTest(janela=nome):
                self.assertEqual(inicio is None, fim is None, "janela pela metade")
                if inicio is not None:
                    self.assertLessEqual(data(inicio), data(fim))

    def test_nucleo_so_existe_com_marco_escolhido(self):
        if self.projeto["janelas"]["nucleo"]["inicio"] is not None:
            self.assertIsNotNone(self.projeto["marco"]["escolhido"])

    def test_campo_ausente_e_null_e_nao_texto_provisorio(self):
        for campo in ("pergunta", "hipoteses"):
            valor = self.projeto[campo]
            if valor is not None:
                self.assertTrue(valor, f"{campo} vazio deve ser null")
                self.assertNotIn("preencher", str(valor).lower())


class Coleta(unittest.TestCase):
    def setUp(self):
        self.coleta = comum.config("coleta")

    def test_gasto_so_com_teto_e_autorizacao(self):
        apify = self.coleta["apify"]
        teto = float(apify["teto_usd"])
        soma = sum(float(valor) for valor in apify["etapas"].values())
        if teto > 0:
            self.assertTrue(apify["autorizacao"].strip(), "teto maior que zero sem frase de autorização")
            self.assertLessEqual(soma, teto + 1e-9)
        else:
            self.assertEqual(soma, 0, "etapa com teto e teto total zero")
            self.assertEqual(apify["autorizacao"].strip(), "", "frase de autorização sem teto")

    def test_etapas_esperadas(self):
        self.assertEqual(set(self.coleta["apify"]["etapas"]), {"teste", "publicacoes", "comentarios", "transcricao", "reserva"})

    def test_segredo_e_so_o_nome(self):
        nomes = [self.coleta["apify"]["segredo"], self.coleta["privado"]["segredo"]]
        nomes += [f["segredo"] for f in self.coleta["gratuitas"].values() if f["segredo"]]
        for nome in nomes:
            self.assertRegex(nome, NOME_DE_SEGREDO)

    def test_frentes_gratuitas_custam_zero(self):
        for chave, frente in self.coleta["gratuitas"].items():
            self.assertEqual(frente["custo_usd"], 0, chave)

    def test_comentarios_tem_modo_decidido_e_mascaras(self):
        regra = self.coleta["comentarios_no_publico"]
        self.assertTrue(regra["modo"].strip())
        self.assertTrue(regra["decisao"].strip())
        self.assertGreaterEqual(len(regra["mascaras"]), 5)


class Atores(unittest.TestCase):
    def test_so_perfil_confirmado_com_fonte(self):
        for perfil in comum.config("atores")["confirmados"]:
            with self.subTest(perfil=perfil.get("id")):
                self.assertTrue(str(perfil.get("confirmado") or "").strip(), "perfil sem confirmação")
                self.assertTrue(perfil.get("redes"), "perfil sem rede")
                for rede, endereco in perfil["redes"].items():
                    self.assertTrue(str(endereco.get("fonte") or "").strip(), f"{rede} sem fonte")


class Termos(unittest.TestCase):
    def setUp(self):
        self.familias = comum.config("termos")["familias"]

    def test_todo_termo_diz_se_e_busca(self):
        for chave, familia in self.familias.items():
            for item in familia["itens"]:
                with self.subTest(familia=chave, termo=item.get("termo")):
                    self.assertTrue(item["termo"].strip())
                    self.assertIsInstance(item["busca"], bool)

    def test_sem_termo_repetido(self):
        vistos = {}
        for chave, familia in self.familias.items():
            for item in familia["itens"]:
                termo = item["termo"].strip().lower()
                self.assertNotIn(termo, vistos, f"'{termo}' em {chave} e em {vistos.get(termo)}")
                vistos[termo] = chave

    def test_homonimo_nunca_e_busca(self):
        for familia in self.familias.values():
            for item in familia["itens"]:
                if item.get("homonimo"):
                    self.assertFalse(item["busca"], f"{item['termo']} é ambíguo demais para virar consulta")

    def test_familia_tem_fonte(self):
        for chave, familia in self.familias.items():
            self.assertTrue(familia["fonte"].strip(), chave)


class DadosPublicos(unittest.TestCase):
    def test_frente_sem_numero_inventado(self):
        ids = set()
        for frente in comum.config("dados_publicos")["frentes"]:
            with self.subTest(frente=frente["id"]):
                self.assertNotIn(frente["id"], ids)
                ids.add(frente["id"])
                self.assertTrue(frente["situacao"].strip())
                self.assertTrue(frente["url"] is None or frente["url"].startswith("https://"))
                if frente["url"] is None:
                    self.assertEqual(frente["situacao"], "não verificado")
                self.assertIsNone(frente["valor"], "valor só entra por coleta com manifesto")


class LivroDeCodigos(unittest.TestCase):
    def test_eixos_e_codigos_unicos(self):
        eixos = comum.config("livro_de_codigos")["eixos"]
        self.assertEqual(len({e["id"] for e in eixos}), len(eixos))
        for eixo in eixos:
            codigos = [c["codigo"] for c in eixo["codigos"]]
            with self.subTest(eixo=eixo["id"]):
                self.assertEqual(len(set(codigos)), len(codigos))
                self.assertTrue(eixo["origem"].strip())
                for codigo in eixo["codigos"]:
                    self.assertTrue(codigo["definicao"].strip())

    def test_tipo_de_conteudo_tem_as_sete_categorias(self):
        eixos = {e["id"]: e for e in comum.config("livro_de_codigos")["eixos"]}
        self.assertEqual(len(eixos["tipo_de_conteudo"]["codigos"]), 7)
        self.assertEqual(len(eixos["qualidade_da_informacao"]["codigos"]), 4)


if __name__ == "__main__":
    unittest.main()
