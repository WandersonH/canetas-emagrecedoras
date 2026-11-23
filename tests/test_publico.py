"""O que o repositório público nunca pode conter."""
import html.parser
import pathlib
import re
import subprocess
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TEXTO = {".py", ".json", ".md", ".html", ".yml", ".yaml", ".txt", ".csv", ".gexf", ".js", ".css"}

CHAVES = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"apify_api_[0-9A-Za-z]{20,}"),
    re.compile(r"gh[pousr]_[0-9A-Za-z]{30,}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
LINK_DE_VENDA = re.compile(r"(?i)\bwa\.me/|api\.whatsapp\.com|chat\.whatsapp\.com|linktr\.ee|\b[\w-]+\.(?:shop|store)\b")
# Outros projetos não são citados como origem. Os nomes ficam em pedaços para o próprio teste não os citar.
OUTROS_PROJETOS = ["od" + "i-" + "influenciadoras", "od" + "i-" + "espanha", "od" + "i-" + "atlas",
                   "od" + "i-" + "secret", "Flavio" + "metro"]


def arquivos_versionaveis():
    """Arquivos de texto do repositório, respeitando o .gitignore quando há git."""
    try:
        saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=RAIZ,
                               capture_output=True, text=True, check=True).stdout.splitlines()
        caminhos = [RAIZ / linha for linha in saida if linha]
    except (OSError, subprocess.CalledProcessError):
        caminhos = [c for c in RAIZ.rglob("*") if ".git" not in c.parts]
    return [c for c in caminhos if c.is_file() and c.suffix.lower() in TEXTO]


class TextoVisivel(html.parser.HTMLParser):
    """Junta o texto que aparece na tela, fora de <script> e <style>."""

    def __init__(self):
        super().__init__()
        self.fora = 0
        self.partes = []

    def handle_starttag(self, tag, atributos):
        if tag in ("script", "style"):
            self.fora += 1
        descricao = tag == "meta" and dict(atributos).get("name") == "description"
        for nome, valor in atributos:
            if not valor:
                continue
            if nome in ("title", "alt", "aria-label", "data-titulo", "data-lide") or (nome == "content" and descricao):
                self.partes.append(valor)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.fora -= 1

    def handle_data(self, dado):
        if not self.fora:
            self.partes.append(dado)


class Publico(unittest.TestCase):
    def test_sem_chave_nem_token(self):
        for caminho in arquivos_versionaveis():
            texto = caminho.read_text(encoding="utf-8", errors="replace")
            for padrao in CHAVES:
                self.assertIsNone(padrao.search(texto), f"parece haver uma chave em {caminho.relative_to(RAIZ)}")

    def test_sem_link_de_venda_fora_dos_testes(self):
        for caminho in arquivos_versionaveis():
            if "tests" in caminho.relative_to(RAIZ).parts:
                continue
            achado = LINK_DE_VENDA.search(caminho.read_text(encoding="utf-8", errors="replace"))
            self.assertIsNone(achado, f"link de venda em {caminho.relative_to(RAIZ)}: {achado.group(0) if achado else ''}")

    def test_nao_cita_outros_projetos_como_origem(self):
        for caminho in arquivos_versionaveis():
            texto = caminho.read_text(encoding="utf-8", errors="replace").lower()
            for nome in OUTROS_PROJETOS:
                self.assertNotIn(nome.lower(), texto, f"{caminho.relative_to(RAIZ)} cita outro projeto")

    def test_pagina_nao_tem_numero_escrito_a_mao(self):
        leitor = TextoVisivel()
        leitor.feed((RAIZ / "index.html").read_text(encoding="utf-8"))
        visivel = " ".join(leitor.partes).replace("GLP-1", "")
        self.assertNotRegex(visivel, r"\d", "número fixo no HTML: todo número deve vir dos arquivos de dados")

    def test_pagina_le_os_arquivos_que_existem(self):
        pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
        nomes = re.findall(r'ler\("([\w/]+)"\)', pagina)
        self.assertTrue(nomes)
        for nome in nomes:
            self.assertTrue((RAIZ / "data" / f"{nome}.json").exists(), f"a página lê data/{nome}.json, que não existe")

    def test_cada_aba_do_menu_tem_secao(self):
        pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
        botoes = re.findall(r'<button type="button" data-aba="(\w+)"', pagina)
        secoes = re.findall(r'<section data-aba="(\w+)"', pagina)
        self.assertEqual(botoes, secoes)

    def test_sem_dado_de_terceiros_no_publico(self):
        proibidas = {"autor", "autor_nome", "autor_canal", "username", "ownerusername"}
        for caminho in (RAIZ / "data").rglob("*.csv"):
            cabecalho = caminho.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
            colunas = {c.strip().lower() for c in (cabecalho[0].split(",") if cabecalho else [])}
            self.assertFalse(colunas & proibidas, f"{caminho.relative_to(RAIZ)} tem coluna de autor")

    def test_workflows_so_com_disparo_manual(self):
        for caminho in (RAIZ / ".github" / "workflows").glob("*.y*ml"):
            texto = caminho.read_text(encoding="utf-8")
            self.assertIn("workflow_dispatch", texto, caminho.name)
            self.assertNotRegex(texto, r"(?m)^\s+(schedule|push|pull_request)\s*:", f"{caminho.name} tem disparo automático")


if __name__ == "__main__":
    unittest.main()
