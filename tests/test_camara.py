"""Proposições da Câmara com arquivo anual de exemplo (sem rede)."""
import io
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import collect_camara as camara  # noqa: E402

CSV = ('"id";"uri";"siglaTipo";"numero";"ano";"ementa";"keywords";"dataApresentacao"\n'
       '"1";"u";"PL";"10";"2025";"Proíbe a venda de canetas emagrecedoras sem receita";"";"2025-05-02T10:00:00"\n'
       '"2";"u";"PL";"11";"2025";"Dispõe sobre o trânsito";"";"2025-05-03T10:00:00"\n'
       '"3";"u";"REQ";"12";"2025";"Requer informações";"SEMAGLUTIDA, OZEMPIC";"2025-06-03T10:00:00"\n')


class Camara(unittest.TestCase):
    def test_filtra_ementa_e_indexacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            (raiz / "data" / "config").mkdir(parents=True)
            for nome in ("termos.json", "projeto.json"):
                (raiz / "data" / "config" / nome).write_text((RAIZ / "data" / "config" / nome).read_text(encoding="utf-8"), encoding="utf-8")
            abrir = lambda url, tempo=None: io.StringIO(CSV) if "2025" in url else (_ for _ in ()).throw(FileNotFoundError(url))  # noqa: E731
            self.assertEqual(camara.main(["--run-id", "1"], abrir=abrir, raiz=raiz), 0)
            saida = json.loads((raiz / "data" / "dados_publicos" / "camara.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(p["id"] for p in saida["proposicoes"]), ["1", "3"])
            self.assertIn("semaglutida", [t for p in saida["proposicoes"] for t in p["termos"]])
            (m,) = [json.loads(x.read_text(encoding="utf-8")) for x in (raiz / "data" / "manifestos").glob("*.json")]
            self.assertEqual(m["universo"]["valor"], 3)  # só o arquivo de 2025 abriu
            self.assertTrue(m["bloqueios"])


if __name__ == "__main__":
    unittest.main()
