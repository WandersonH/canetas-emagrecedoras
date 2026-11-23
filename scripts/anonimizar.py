"""Anonimização do texto de terceiros antes de ir para a página pública.

Tema de saúde: relato de uso, peso, doença ou efeito colateral de pessoa comum é dado sensível.
O que este módulo faz com cada texto:
- troca menções com arroba por [perfil];
- troca links por [link] (isso também impede que link de venda chegue ao público);
- troca telefones por [telefone] e e-mails por [e-mail];
- troca todo número por [n], o que cobre dose, peso, idade, preço e data;
- preserva nomes de produto que têm número e não identificam ninguém (lista em PRESERVAR).

O autor vira um código (A0001, A0002...) na ordem em que aparece. A tabela que liga autor a código
só pode ser gravada no repositório privado.

Limites conhecidos, que a revisão humana cobre:
- nome de pessoa escrito por extenso dentro do texto não é detectado;
- uma frase longa e incomum ainda pode ser achada pela busca da própria plataforma.
"""
from __future__ import annotations

import re

PRESERVAR = ("GLP-1", "GLP1", "T36")
_MARCADOR = 0xE000  # início da área de uso privado do Unicode
_LIMITE = 6400  # tamanho dessa área

_LINK = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|shop|store|app|io|me|ly|br)(?:\.br)?(?:/\S*)?")
_EMAIL = re.compile(r"(?i)\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_PERFIL = re.compile(r"(?<![\w@])@[\w.]{2,}")
_TELEFONE = re.compile(
    r"(?<!\w)(?:\+?55[\s.-]?)?\(?\d{2}\)?[\s.-]?9?\d{4}[\s.-]?\d{4}(?!\w)"  # com DDD
    r"|(?<!\w)9\d{4}[\s.-]?\d{4}(?!\w)"  # celular sem DDD
)
_NUMERO = re.compile(r"\d+(?:[.,:/]\d+)*")
_ESPACO = re.compile(r"[ \t]{2,}")


def anonimizar_texto(texto: str) -> str:
    """Devolve o texto sem perfis, links, telefones, e-mails e números."""
    if not texto:
        return ""
    guardados: list[str] = []

    def guardar(achado: re.Match) -> str:
        # Marcador sem dígito (área de uso privado do Unicode), para a troca de números não o atingir.
        guardados.append(achado.group(0))
        return chr(_MARCADOR + len(guardados) - 1)

    saida = "".join(letra for letra in texto if not _MARCADOR <= ord(letra) < _MARCADOR + _LIMITE)
    saida = _EMAIL.sub("[e-mail]", saida)
    saida = _LINK.sub("[link]", saida)
    saida = _PERFIL.sub("[perfil]", saida)
    saida = _TELEFONE.sub("[telefone]", saida)
    padrao_preservar = re.compile("|".join(re.escape(termo) for termo in PRESERVAR), re.IGNORECASE)
    saida = padrao_preservar.sub(guardar, saida)
    saida = _NUMERO.sub("[n]", saida)
    for indice, original in enumerate(guardados[:_LIMITE]):
        saida = saida.replace(chr(_MARCADOR + indice), original)
    return _ESPACO.sub(" ", saida).strip()


def codigos_de_autores(autores: list[str]) -> dict[str, str]:
    """Atribui A0001, A0002... na ordem da primeira aparição. Autor vazio não recebe código."""
    tabela: dict[str, str] = {}
    for autor in autores:
        chave = (autor or "").strip().lower()
        if chave and chave not in tabela:
            tabela[chave] = f"A{len(tabela) + 1:04d}"
    return tabela


def tem_resto_identificavel(texto: str) -> list[str]:
    """Lista o que ainda parece identificável num texto já anonimizado. Lista vazia é o esperado."""
    sem_preservados = texto
    for termo in PRESERVAR:
        sem_preservados = re.sub(re.escape(termo), "", sem_preservados, flags=re.IGNORECASE)
    restos = []
    if re.search(r"\d", sem_preservados):
        restos.append("número")
    if _PERFIL.search(texto):
        restos.append("perfil")
    if re.search(r"(?i)https?://|www\.", texto):
        restos.append("link")
    if _EMAIL.search(texto):
        restos.append("e-mail")
    return restos
