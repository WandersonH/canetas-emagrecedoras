"""Coletor dos dados abertos da Anvisa, com arquivos de exemplo (nenhuma chamada de rede)."""
import io
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import collect_anvisa as anvisa  # noqa: E402

REGISTRO = ("TIPO_PRODUTO;NOME_PRODUTO;PRINCIPIO_ATIVO;EMPRESA_DETENTORA_REGISTRO;SITUACAO_REGISTRO\n"
            "MEDICAMENTO;OZEMPIC;SEMAGLUTIDA;EMPRESA A;VÁLIDO\n"
            "MEDICAMENTO;DIPIRONA X;DIPIRONA;EMPRESA B;VÁLIDO\n"
            "MEDICAMENTO;MOUNJARO;TIRZEPATIDA;EMPRESA C;VÁLIDO\n")
MEDICAMENTOS = ("IDENTIFICACAO_NOTIFICACAO;NOME_MEDICAMENTO_WHODRUG;RELACAO_MEDICAMENTO_EVENTO\n"
                "N1;Ozempic;Suspeito\nN2;Paracetamol;Suspeito\nN3;Saxenda;Concomitante\nN1;Losartana;Concomitante\n")
NOTIFICACOES = ("UF;IDENTIFICACAO_NOTIFICACAO;DATA_INCLUSAO_SISTEMA;DATA_NOTIFICACAO;SEXO;GRUPO_IDADE;GRAVE\n"
                "SP;N1;15/03/2025;;Feminino;Adulto;Não\nRJ;N2;01/02/2025;;Masculino;Idoso;Sim\nMG;N3;01/01/2026;10/07/2026;Feminino;Adulto;Sim\n")
REACOES = "IDENTIFICACAO_NOTIFICACAO;PT\nN1;Náusea\nN2;Cefaleia\nN3;Náusea\nN3;Vômito\n"
INDICE = ('<a href="?C=N">Name</a><a href="/dados/SNGPC/">Parent Directory</a>'
          '<a href="EDA_Industrializados_202412.csv">EDA_Industrializados_202412.csv</a> 2026-06-14 16:25 1G'
          '<a href="EDA_Industrializados_202601.csv">EDA_Industrializados_202601.csv</a> 2026-11-22 15:26 1G')
SNGPC = ("NU_ANO_VENDA;NU_MES_VENDA;SG_UF_VENDA;DS_PRINCIPIO_ATIVO;QT_VENDIDA;SG_SEXO;NU_IDADE\n"
         + "".join(f"2026;1;SP;SEMAGLUTIDA;2;2;40\n" for _ in range(6))
         + "2026;1;RJ;TIRZEPATIDA;1;1;35\n2026;1;SP;AMOXICILINA;9;1;20\n")


def abridor(arquivos: dict[str, str]):
    def abrir(url, tempo=None):
        for nome, conteudo in arquivos.items():
            if url.endswith(nome):
                return io.StringIO(conteudo)
        raise FileNotFoundError(url)
    return abrir


class Anvisa(unittest.TestCase):
    def setUp(self):
        self.chaves = anvisa.chaves(RAIZ)
        self.pat = anvisa.padrao(self.chaves)
        self.tmp = tempfile.TemporaryDirectory()
        self.publico = pathlib.Path(self.tmp.name) / "publico"
        self.privado = pathlib.Path(self.tmp.name) / "privado"
        (self.publico / "data" / "config").mkdir(parents=True)
        for nome in ("termos.json", "projeto.json"):
            (self.publico / "data" / "config" / nome).write_text((RAIZ / "data" / "config" / nome).read_text(encoding="utf-8"),
                                                              encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def manifestos(self):
        return [json.loads(p.read_text(encoding="utf-8")) for p in (self.publico / "data" / "manifestos").glob("*.json")]

    def test_chaves_trazem_substancias_e_marcas(self):
        for k in ("SEMAGLUTIDA", "TIRZEPATIDA", "OZEMPIC", "MOUNJARO", "RETATRUTIDA"):
            self.assertIn(k, self.chaves)

    def test_codificacao_e_separador(self):
        self.assertEqual(anvisa.codificacao("ação".encode("latin-1")), "latin-1")
        self.assertEqual(anvisa.codificacao("ação".encode("utf-8")), "utf-8-sig")
        self.assertEqual(anvisa.separador("A;B;C"), ";")
        self.assertEqual(anvisa.separador("A,B,C"), ",")

    def test_registro_filtra_e_conta_universo(self):
        anvisa.ARQUIVOS["registro"] = ["DADOS_ABERTOS_MEDICAMENTOS.csv"]
        saida = anvisa.frente_tabela("registro", self.chaves, self.pat, "1",
                                     abridor({"DADOS_ABERTOS_MEDICAMENTOS.csv": REGISTRO}), raiz=self.publico)
        arquivo = saida["arquivos"][0]
        self.assertEqual(arquivo["linhas_no_arquivo"], 3)
        self.assertEqual(arquivo["linhas_que_citam"], 2)
        (m,) = self.manifestos()
        self.assertEqual(m["universo"]["valor"], 3)
        self.assertEqual(m["amostra"]["n"], 2)
        self.assertEqual(m["parou_por"], "arquivo_inteiro")

    def test_arquivo_que_falha_fica_ausente_e_nao_zero(self):
        saida = anvisa.frente_tabela("cmed", self.chaves, self.pat, "1", abridor({}), raiz=self.publico)
        self.assertTrue(all(a["linhas_no_arquivo"] is None for a in saida["arquivos"]))
        (m,) = self.manifestos()
        self.assertIsNone(m["universo"]["valor"])
        self.assertIsNone(m["lido"])
        self.assertTrue(m["bloqueios"])

    def test_vigimed_junta_por_notificacao_e_guarda_linhas_no_privado(self):
        arquivos = {"VigiMed_Medicamentos.csv": MEDICAMENTOS, "VigiMed_Notificacoes.csv": NOTIFICACOES,
                    "VigiMed_Reacoes.csv": REACOES}
        saida = anvisa.frente_vigimed(self.chaves, self.pat, "1", self.privado, abridor(arquivos), raiz=self.publico)
        self.assertEqual(saida["notificacoes"], 2)  # N1 e N3
        self.assertTrue((self.privado / "dados_publicos" / "vigimed" / "notificacoes.csv").exists())
        publico = (self.publico / "data" / "dados_publicos" / "vigimed.json").read_text(encoding="utf-8")
        self.assertNotIn("N1", publico)  # identificador de notificação não vai ao público
        self.assertNotIn('"N3"', publico)
        # contagens pequenas mascaradas
        self.assertIn('"<5"', publico)
        self.assertEqual(saida["coluna_da_reacao"], "PT")
        # data da notificação vazia: vale a data de inclusão no sistema
        self.assertEqual({x["valor"] for x in saida["por_ano"]}, {"2025", "2026"})
        # marca conta pela substância
        self.assertEqual({x["valor"] for x in saida["por_substancia"]}, {"semaglutida", "liraglutida"})

    def test_sngpc_le_so_meses_do_periodo_e_agrega(self):
        pagina = {"http": 200, "corpo": INDICE.encode()}
        meses = anvisa.meses_sngpc("industrializados", "202501", lambda url: pagina)
        self.assertEqual([m for m, _ in meses], ["202601"])
        saida = anvisa.frente_sngpc("industrializados", self.chaves, self.pat, "1", self.privado, "202501",
                                    abridor({"_202601.csv": SNGPC}), lambda url: pagina, raiz=self.publico)
        linhas = {(r["mes"], r["substancia"]): r for r in saida["por_mes_e_substancia"]}
        self.assertEqual(linhas[("2026-01", "semaglutida")]["linhas"], 6)
        self.assertEqual(linhas[("2026-01", "semaglutida")]["quantidade"], 12)
        self.assertEqual(linhas[("2026-01", "tirzepatida")]["linhas"], "<5")
        self.assertIsNone(linhas[("2026-01", "tirzepatida")]["quantidade"])
        (m,) = self.manifestos()
        arquivo = self.privado / "dados_publicos" / "sngpc_industrializados" / "202601.csv.gz"
        import gzip
        with gzip.open(arquivo, "rt", encoding="utf-8") as f:
            self.assertEqual(len(f.read().strip().splitlines()), 8)  # cabeçalho + 7 linhas
        self.assertEqual([a["caminho"] for a in m["arquivos_privados"]], ["dados_publicos/sngpc_industrializados/202601.csv.gz"])
        self.assertEqual(m["universo"]["valor"], 8)
        self.assertEqual(m["amostra"]["n"], 7)


if __name__ == "__main__":
    unittest.main()
