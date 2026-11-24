"""Proposições da Câmara com respostas de exemplo (sem rede)."""
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import collect_camara as camara  # noqa: E402


class Camara(unittest.TestCase):
    def test_pagina_e_total(self):
        paginas = {1: [{"id": i} for i in range(100)], 2: [{"id": 100 + i} for i in range(20)]}

        def leitor(url):
            n = int(url.split("pagina=")[1].split("&")[0])
            return {"dados": paginas.get(n, [])}, 120
        itens, total, parou = camara.consultar("semaglutida", "2025-01-01", "2026-11-23", leitor)
        self.assertEqual((len(itens), total, parou), (120, 120, "fim_dos_resultados"))

    def test_junta_termos_e_universo_soma_totais(self):
        def leitor(url):
            return {"dados": [{"id": 7, "siglaTipo": "PL", "numero": 1, "ano": 2025, "ementa": "x"}]}, 1
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            (raiz / "data" / "config").mkdir(parents=True)
            for nome in ("termos.json", "projeto.json"):
                (raiz / "data" / "config" / nome).write_text((RAIZ / "data" / "config" / nome).read_text(encoding="utf-8"), encoding="utf-8")
            self.assertEqual(camara.main(["--run-id", "1"], leitor=leitor, raiz=raiz), 0)
            import json
            saida = json.loads((raiz / "data" / "dados_publicos" / "camara.json").read_text(encoding="utf-8"))
            self.assertEqual(len(saida["proposicoes"]), 1)
            self.assertEqual(len(saida["proposicoes"][0]["termos"]), len(camara.palavras(raiz)))


if __name__ == "__main__":
    unittest.main()
