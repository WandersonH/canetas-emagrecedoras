"""Transcrição: escolha dos vídeos e leitura da duração, sem rede e sem modelo."""
import csv
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import collect_transcricoes as ct  # noqa: E402


class Transcricoes(unittest.TestCase):
    def test_duracao_iso(self):
        self.assertEqual(ct.duracao_iso("PT1M2S"), 62)
        self.assertEqual(ct.duracao_iso("PT1H"), 3600)
        self.assertIsNone(ct.duracao_iso(""))
        self.assertIsNone(ct.duracao_iso("P"))

    def test_kwai_usa_endereco_direto_e_ordena_por_vistas(self):
        with tempfile.TemporaryDirectory() as tmp:
            privado = pathlib.Path(tmp)
            (privado / "terceiros" / "kwai").mkdir(parents=True)
            with (privado / "terceiros" / "kwai" / "publicacoes_x.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["item_id", "conta", "publicado_em", "visualizacoes", "url", "texto"])
                w.writeheader()
                w.writerow({"item_id": "k1", "publicado_em": "2025-03-01", "visualizacoes": "5", "url": "https://k/1"})
                w.writerow({"item_id": "k2", "publicado_em": "2025-03-01", "visualizacoes": "50", "url": ""})
                w.writerow({"item_id": "k3", "publicado_em": "2024-03-01", "visualizacoes": "500", "url": "https://k/3"})
            (privado / "bruto" / "kwai").mkdir(parents=True)
            (privado / "bruto" / "kwai" / "p.json").write_text(json.dumps([{"videoId": "k2", "videoUrl": "https://cdn/k2.mp4"}]))
            lista = ct.videos(privado, "kwai", "2025-01-01", "2026-11-23")
            self.assertEqual([v["item_id"] for v in lista], ["k2", "k1"])
            self.assertEqual(lista[0]["arquivo"], "https://cdn/k2.mp4")


if __name__ == "__main__":
    unittest.main()
