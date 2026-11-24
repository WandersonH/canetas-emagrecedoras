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
        visivel = " ".join(leitor.partes)
        for nome_com_numero in ("GLP-1", "ForceAtlas 2"):  # nomes próprios, não dados
            visivel = visivel.replace(nome_com_numero, "")
        self.assertNotRegex(visivel, r"\d", "número fixo no HTML: todo número deve vir dos arquivos de dados")

    def test_pagina_le_os_arquivos_que_existem(self):
        pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
        nomes = re.findall(r'ler\("([\w/]+)"\)', pagina)
        self.assertTrue(nomes)
        for nome in nomes:
            self.assertTrue((RAIZ / "data" / f"{nome}.json").exists(), f"a página lê data/{nome}.json, que não existe")

    def test_cada_aba_do_menu_tem_secao(self):
        pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
        botoes = re.findall(r'<button class="navbutton[^"]*" data-tab="(\w+)"', pagina)
        secoes = re.findall(r'<section class="panel[^"]*" id="(\w+)"', pagina)
        self.assertTrue(botoes)
        self.assertEqual(botoes, secoes)

    def test_pagina_usa_a_folha_de_estilo_do_projeto(self):
        pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./assets/atlas.css"', pagina)
        for arquivo in ("atlas.css", "marca.jpg", "favicon.ico"):
            self.assertTrue((RAIZ / "assets" / arquivo).exists(), arquivo)

    def test_sem_dado_de_terceiros_no_publico(self):
        proibidas = {"autor", "autor_nome", "autor_canal", "username", "ownerusername"}
        for caminho in (RAIZ / "data").rglob("*.csv"):
            cabecalho = caminho.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
            colunas = {c.strip().lower() for c in (cabecalho[0].split(",") if cabecalho else [])}
            self.assertFalse(colunas & proibidas, f"{caminho.relative_to(RAIZ)} tem coluna de autor")

    def test_segredo_so_entra_por_variavel_de_ambiente(self):
        for caminho in (RAIZ / ".github" / "workflows").glob("*.y*ml"):
            for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
                if "secrets." in linha:
                    self.assertRegex(linha.strip(), r"^[A-Z_]+: \$\{\{ secrets\.[A-Z_]+ \}\}$", f"{caminho.name}:{numero}")

    def test_changelog_sem_marca_de_conflito_e_com_as_cinco_secoes(self):
        texto = (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertNotRegex(texto, r"(?m)^(<<<<<<<|=======|>>>>>>>)", "conflito de merge não resolvido no CHANGELOG")
        entradas = re.split(r"(?m)^## ", texto)[1:]
        self.assertTrue(entradas)
        for entrada in entradas:
            for rotulo in ("O que mudou", "Por quê", "O que foi executado de verdade", "O que ficou pendente", "Onde está a evidência"):
                self.assertIn(f"**{rotulo}**", entrada, entrada.splitlines()[0])

    def test_corpus_publico_de_terceiros_esta_anonimizado(self):
        import json
        caminho = RAIZ / "data" / "corpus" / "segmentos.json"
        if not caminho.exists():
            self.skipTest("corpus ainda não gerado")
        for s in json.loads(caminho.read_text(encoding="utf-8")):
            if s["f"] in ("imprensa", "checagens"):
                continue
            texto = re.sub(r"(?i)glp-?1|t36", "", s["t"])
            self.assertNotRegex(texto, r"(?<![A-Za-zÀ-ú])\d|(?<![A-Za-zÀ-ú])@\w|https?://|www\.", f"segmento {s['i']} de terceiro com dado identificável")
            self.assertIsNone(s["u"], f"segmento {s['i']} de terceiro com link")
            self.assertRegex(s["a"] or "A0000", r"^A\d{4,}$", f"segmento {s['i']} de terceiro sem código de autor")

    def test_json_publico_e_json_valido(self):
        """NaN e Infinity quebram a leitura no navegador: medida indefinida tem de sair como null (⛔)."""
        import json

        def recusa(c):
            raise ValueError(c)
        for caminho in (RAIZ / "data").rglob("*.json"):
            try:
                json.loads(caminho.read_text(encoding="utf-8"), parse_constant=recusa)
            except ValueError as erro:
                self.fail(f"{caminho.relative_to(RAIZ)} não é JSON válido: {erro}")

    def test_corpus_de_comentarios_esta_anonimizado(self):
        import json
        arquivos = sorted((RAIZ / "data" / "comentarios").glob("*_corpus.json"))
        if not arquivos:
            self.skipTest("cadernos de comentários ainda não gerados")
        for caminho in arquivos:
            for c in json.loads(caminho.read_text(encoding="utf-8")):
                texto = re.sub(r"(?i)glp-?1|t36", "", c["t"])
                self.assertNotRegex(texto, r"(?<![A-Za-zÀ-ú])\d|(?<![A-Za-zÀ-ú])@\w|https?://|www\.", f"{caminho.name} item {c['i']} com dado identificável")
                self.assertRegex(c["a"] or "A0000", r"^[AC]\d{4,}$", f"{caminho.name} item {c['i']} sem código de autor")
                self.assertRegex(c["p"], r"^P\d{3,}$", f"{caminho.name} item {c['i']} com identificador da publicação")
                self.assertEqual(set(c), {"i", "a", "d", "k", "c", "s", "p", "t"}, f"{caminho.name}: campo inesperado")

    def test_redes_de_comentarios_so_com_codigos(self):
        import json
        for caminho in sorted((RAIZ / "data" / "comentarios").glob("*.json")):
            if caminho.name.endswith("_corpus.json") or caminho.name in ("resumo.json", "analise.json"):
                continue
            m = json.loads(caminho.read_text(encoding="utf-8")).get("mencoes") or {}
            for n in m.get("nos", []):
                self.assertRegex(n["id"], r"^[ACM]\d{4,}$", f"{caminho.name}: nó de menção sem código")
                self.assertEqual(n["id"], n["rotulo"], f"{caminho.name}: rótulo de menção diferente do código")

    def test_jama_publico_so_tem_agregados(self):
        import json
        caminho = RAIZ / "data" / "jama" / "manual.json"
        if not caminho.exists():
            self.skipTest("agregados JAMA ainda não gerados")
        texto = caminho.read_text(encoding="utf-8")
        self.assertNotRegex(texto, r"https?://|tiktok\.com|@\w", "agregado JAMA com link ou perfil")
        dado = json.loads(texto)
        self.assertNotIn("videos_lista", dado)
        for g in dado["por_tipo_de_perfil"] + dado["por_tipo_de_caneta"]:
            self.assertEqual(set(g) - {"grupo", "videos", "pontuacao_media", "autoria", "atribuicao", "divulgacao", "atualidade"}, set())

    def test_workflows_so_com_disparo_manual(self):
        for caminho in (RAIZ / ".github" / "workflows").glob("*.y*ml"):
            texto = caminho.read_text(encoding="utf-8")
            self.assertIn("workflow_dispatch", texto, caminho.name)
            self.assertNotRegex(texto, r"(?m)^\s+(schedule|push|pull_request)\s*:", f"{caminho.name} tem disparo automático")


if __name__ == "__main__":
    unittest.main()
