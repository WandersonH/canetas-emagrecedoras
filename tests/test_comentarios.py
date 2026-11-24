"""Coletor de comentários, sem rede: escolha das publicações, normalização e trava de gasto."""
import csv
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import autorizacao  # noqa: E402
import collect_comentarios as cc  # noqa: E402

APIFY = {"teto_usd": 10, "autorizacao": "frase de teste", "etapas": {"comentarios": 1.0}}


def escrever(caminho: pathlib.Path, campos, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


class Comentarios(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.privado = pathlib.Path(self.tmp.name)
        campos = ["rede", "item_id", "conta", "publicado_em", "texto", "visualizacoes", "curtidas", "comentarios",
                  "compartilhamentos", "url", "termos"]
        escrever(self.privado / "terceiros" / "tiktok" / "publicacoes_x.csv", campos, [
            {"rede": "tiktok", "item_id": "1", "publicado_em": "2025-05-01", "comentarios": "10", "url": "https://t/1"},
            {"rede": "tiktok", "item_id": "2", "publicado_em": "2025-05-01", "comentarios": "300", "url": "https://t/2"},
            {"rede": "tiktok", "item_id": "3", "publicado_em": "2024-05-01", "comentarios": "900", "url": "https://t/3"},
            {"rede": "tiktok", "item_id": "4", "publicado_em": "2025-06-01", "comentarios": "0", "url": "https://t/4"}])
        escrever(self.privado / "terceiros" / "tiktok" / "teste_x.csv", campos, [
            {"rede": "tiktok", "item_id": "9", "publicado_em": "2025-05-01", "comentarios": "9999", "url": "https://t/9"}])
        escrever(self.privado / "terceiros" / "youtube" / "videos_x.csv",
                 ["video_id", "publicado_em", "titulo", "comentarios"], [
                     {"video_id": "a", "publicado_em": "2025-02-01", "titulo": "Como a caneta funciona para emagrecer", "comentarios": "50"},
                     {"video_id": "b", "publicado_em": "2025-02-01", "titulo": "How weight loss shots work for you", "comentarios": "80"}])

    def tearDown(self):
        self.tmp.cleanup()

    def test_escolhe_periodo_com_comentarios_e_ignora_teste(self):
        escolhidas = cc.escolher(self.privado, "tiktok", 5, "2025-01-01", "2026-11-23")
        self.assertEqual([p["item_id"] for p in escolhidas], ["2", "1"])

    def test_youtube_so_em_portugues(self):
        escolhidas = cc.escolher(self.privado, "youtube", 5, "2025-01-01", "2026-11-23")
        self.assertEqual([p["item_id"] for p in escolhidas], ["a"])

    def test_normaliza_tiktok_e_descarta_vazio(self):
        alvo = {"7400"}
        linha = cc.normalizar("tiktok", {"cid": "c1", "videoWebUrl": "https://www.tiktok.com/@x/video/7400", "uniqueId": "u",
                                          "text": " oi  tudo ", "createTime": 1735700000, "diggCount": 3}, alvo)
        self.assertEqual(linha["item_id"], "7400")
        self.assertEqual(linha["texto"], "oi tudo")
        self.assertIsNone(cc.normalizar("tiktok", {"cid": "c2", "text": ""}, alvo))

    def test_x_descarta_a_propria_publicacao(self):
        self.assertIsNone(cc.normalizar("x", {"id": "55", "conversationId": "55", "text": "post"}, {"55"}))
        self.assertIsNotNone(cc.normalizar("x", {"id": "56", "conversationId": "55", "text": "resposta"}, {"55"}))

    def test_apify_respeita_teto_da_etapa(self):
        cfg = {"ator": "a~b", "preco_item": 0.01, "por_publicacao": 10}
        pubs = [{"item_id": str(i), "url": f"https://t/{i}", "comentarios": 5} for i in range(50)]
        chamadas = []

        def executar(ator, entrada, teto):
            chamadas.append((entrada, teto))
            return {"id": "r", "status": "SUCCEEDED", "usageTotalUsd": 0.5}, []
        _, _, resumo, _ = cc.apify_rede("tiktok", cfg, pubs, APIFY, executar, gasto_antes=0.0)
        self.assertLessEqual(resumo["previsto_usd"], 1.0)
        self.assertLess(resumo["publicacoes_pedidas"], 50)
        self.assertLessEqual(chamadas[0][1], 1.0)

    def test_sem_sobra_nao_chama_a_apify(self):
        cfg = {"ator": "a~b", "preco_item": 0.01, "por_publicacao": 10}
        pubs = [{"item_id": "1", "url": "https://t/1", "comentarios": 5}]
        executar = lambda *a: self.fail("não devia chamar")  # noqa: E731
        linhas, _, resumo, gasto = cc.apify_rede("tiktok", cfg, pubs, APIFY, executar, gasto_antes=1.0)
        self.assertEqual((linhas, gasto), ([], 0.0))
        self.assertIn("⛔", resumo["situacao"])

    def test_frase_vazia_bloqueia(self):
        cfg = {"ator": "a~b", "preco_item": 0.001, "por_publicacao": 10}
        pubs = [{"item_id": "1", "url": "https://t/1", "comentarios": 5}]
        with self.assertRaises(autorizacao.GastoNaoAutorizado):
            cc.apify_rede("tiktok", cfg, pubs, {**APIFY, "autorizacao": ""}, lambda *a: None, gasto_antes=0.0)


if __name__ == "__main__":
    unittest.main()
