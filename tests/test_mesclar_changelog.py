"""Junção de CHANGELOG em conflito: nenhuma entrada se perde."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import mesclar_changelog as mc  # noqa: E402

BASE = "# CHANGELOG\n\nTopo.\n\n## velho\n\nx\n"


class Mesclar(unittest.TestCase):
    def test_mantem_as_duas_entradas(self):
        remoto = BASE.replace("## velho", "## A\n\na\n\n## velho")
        meu = BASE.replace("## velho", "## B\n\nb\n\n## velho")
        saida = mc.mesclar(remoto, meu)
        self.assertEqual([l for l in saida.splitlines() if l.startswith("## ")], ["## B", "## A", "## velho"])

    def test_nao_duplica(self):
        meu = BASE.replace("## velho", "## B\n\nb\n\n## velho")
        self.assertEqual(mc.mesclar(meu, meu), meu)


if __name__ == "__main__":
    unittest.main()
