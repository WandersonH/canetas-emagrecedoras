"""Transcrição da fala dos vídeos já coletados, com Whisper (faster-whisper) no próprio runner, sem custo.

Quais vídeos: os do período lido com mais visualizações informadas, por rede (TikTok, Kwai e YouTube), até N por
rede e até a duração máxima. O áudio é baixado com yt-dlp (página do vídeo) ou pelo endereço direto do arquivo
quando o bruto da coleta o traz (Kwai). Vídeo que não baixa fica registrado com o motivo.

Universo: vídeos da rede já coletados no período (repositório privado). Lido: vídeos tentados.
Amostra: vídeos transcritos. É uma amostra intencional (os mais vistos), não aleatória.

Privacidade: a transcrição é texto de terceiros e fica só no privado (terceiros/transcricoes/). No público entra
anonimizada pelo corpus (scripts/build_corpus.py); aqui só contagens em data/transcricoes/resumo.json.

Uso:
    python scripts/collect_transcricoes.py --privado DIR --redes tiktok kwai youtube --run-id 123
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import collect_comentarios  # noqa: E402
import collect_redes  # noqa: E402
import comum  # noqa: E402
import rede  # noqa: E402

PADRAO = {"modelo": "small", "duracao_maxima_s": 600, "tiktok": 60, "kwai": 20, "youtube": 30}
CAMPOS = ["rede", "item_id", "conta", "publicado_em", "duracao_s", "idioma", "texto", "modelo"]


def configuracao(coleta: dict) -> dict:
    return {**PADRAO, **(coleta.get("transcricao") or {})}


def videos(privado: pathlib.Path, rede_id: str, inicio: str, fim: str) -> list[dict]:
    """Vídeos da rede no período, sem repetição, do mais visto ao menos visto."""
    por_id: dict[str, dict] = {}
    if rede_id == "semente":  # vídeos da planilha-semente JAMA, para a fala completa; sem filtro de data
        return videos_semente(privado)
    if rede_id == "youtube":
        for caminho in sorted(glob.glob(str(privado / "terceiros" / "youtube" / "*.csv"))):
            for r in collect_comentarios.ler_csv(caminho):
                if r.get("video_id"):
                    por_id[r["video_id"]] = {"item_id": r["video_id"], "conta": r.get("canal_id") or "",
                                             "data": (r.get("publicado_em") or "")[:10],
                                             "vistas": collect_redes.inteiro(r.get("visualizacoes")),
                                             "duracao_s": duracao_iso(r.get("duracao")),
                                             "pagina": f"https://www.youtube.com/watch?v={r['video_id']}", "arquivo": None,
                                             "titulo": r.get("titulo") or ""}
    else:
        diretos = enderecos_diretos(privado, rede_id)
        for caminho in sorted(glob.glob(str(privado / "terceiros" / rede_id / "*.csv"))):
            if "/teste_" in caminho.replace("\\", "/"):
                continue
            for r in collect_comentarios.ler_csv(caminho):
                if r.get("item_id"):
                    por_id[r["item_id"]] = {"item_id": r["item_id"], "conta": r.get("conta") or "",
                                            "data": (r.get("publicado_em") or "")[:10],
                                            "vistas": collect_redes.inteiro(r.get("visualizacoes")), "duracao_s": None,
                                            "pagina": r.get("url"), "arquivo": diretos.get(r["item_id"]), "titulo": r.get("texto") or ""}
    lista = [v for v in por_id.values() if v["data"] and inicio <= v["data"] <= fim and (v["pagina"] or v["arquivo"])]
    if rede_id == "youtube":
        lista = [v for v in lista if collect_comentarios._portugues(v["titulo"])]
    return sorted(lista, key=lambda v: (-(v["vistas"] or 0), v["item_id"]))


def videos_semente(privado: pathlib.Path) -> list[dict]:
    """Endereços da planilha-semente (codificação manual JAMA), um por vídeo, na ordem da planilha."""
    import openpyxl
    cfg = comum.config("jama")
    ws = openpyxl.load_workbook(privado / cfg["semente"], read_only=True, data_only=True)[cfg["aba"]]
    rows = list(ws.iter_rows(values_only=True))
    cab = [str(c).strip() if c is not None else "" for c in rows[0]]
    saida, vistos = [], set()
    for r in rows[1:]:
        d = dict(zip(cab, r))
        url = str(d.get("URL") or "").strip()
        if not url.startswith("https://") or url in vistos:
            continue
        vistos.add(url)
        achado = re.search(r"/video/(\d+)", url)
        item = str(d.get("ID do vídeo") or "").strip() or (achado.group(1) if achado else f"semente_linha_{d.get('Nº')}")
        conta = re.search(r"tiktok\.com/@([^/?]+)", url)
        saida.append({"item_id": item, "conta": conta.group(1) if conta else "", "data": str(d.get("Data") or "")[:10],
                      "vistas": None, "duracao_s": None, "pagina": url, "arquivo": None, "titulo": ""})
    return saida


def ja_transcritos(privado: pathlib.Path, rede_id: str) -> set[str]:
    """Vídeos que já têm transcrição com texto no privado: não são baixados de novo."""
    feitos = set()
    for caminho in glob.glob(str(privado / "terceiros" / "transcricoes" / rede_id / "*.csv")):
        for r in collect_comentarios.ler_csv(caminho):
            if (r.get("texto") or "").strip():
                feitos.add(r["item_id"])
    return feitos


def duracao_iso(texto: str | None) -> int | None:
    """'PT1M2S' -> 62."""
    import re
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", (texto or "").strip())
    if not m or not any(m.groups()):
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def enderecos_diretos(privado: pathlib.Path, rede_id: str) -> dict[str, str]:
    """Endereço direto do arquivo de vídeo, quando o bruto da coleta traz (Kwai)."""
    saida = {}
    for caminho in sorted(glob.glob(str(privado / "bruto" / rede_id / "*.json"))):
        try:
            itens = json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for x in itens if isinstance(itens, list) else []:
            iid = collect_redes.g(x, "videoId", "video_id", "photoId", "id")
            arquivo = collect_redes.g(x, "videoUrl", "mp4Url", "playUrl")
            if iid and arquivo and str(arquivo).startswith("http"):
                saida[str(iid)] = str(arquivo)
    return saida


def baixar_audio(video: dict, pasta: pathlib.Path, duracao_maxima: int) -> pathlib.Path:
    destino = pasta / f"{video['item_id']}"
    if video.get("arquivo"):
        bruto = destino.with_suffix(".mp4")
        pedido = urllib.request.Request(video["arquivo"], headers={"User-Agent": rede.AGENTE})
        with urllib.request.urlopen(pedido, timeout=120) as resposta, bruto.open("wb") as saida:
            saida.write(resposta.read())
        return bruto
    comando = [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "--no-playlist", "-f", "bestaudio/best",
               "--match-filter", f"duration <= {duracao_maxima}", "-o", str(destino) + ".%(ext)s", video["pagina"]]
    r = subprocess.run(comando, capture_output=True, text=True, timeout=300)
    achados = sorted(pasta.glob(f"{video['item_id']}.*"))
    if not achados:
        motivo = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["sem arquivo (duração acima do limite ou bloqueio)"]
        raise RuntimeError(motivo[0][:200])
    return achados[0]


def audio_16k(arquivo: pathlib.Path):
    """Áudio mono a 16 kHz pelo ffmpeg, sem depender do decodificador embutido do faster-whisper."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(arquivo), "-f", "s16le", "-ac", "1",
                        "-ar", "16000", "-"], capture_output=True, timeout=600)
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError("ffmpeg: " + (r.stderr.decode("utf-8", "replace").strip().splitlines() or ["sem áudio"])[-1][:150])
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def transcrever(modelo, arquivo: pathlib.Path) -> tuple[str, str, float]:
    audio = audio_16k(arquivo)
    segmentos, info = modelo.transcribe(audio, language="pt", vad_filter=True, beam_size=1)
    texto = " ".join(s.text.strip() for s in segmentos)
    return " ".join(texto.split()), info.language, round(len(audio) / 16000, 1)


def main(argumentos=None) -> int:
    leitor = argparse.ArgumentParser(description="Transcrição dos vídeos mais vistos, com Whisper.")
    leitor.add_argument("--privado", required=True)
    leitor.add_argument("--redes", nargs="*", default=["tiktok", "kwai", "youtube"])
    leitor.add_argument("--run-id", default=None)
    leitor.add_argument("--minutos", type=float, default=200, help="para de começar vídeos novos depois deste tempo")
    opcoes = leitor.parse_args(argumentos)
    privado = pathlib.Path(opcoes.privado)
    cfg = configuracao(comum.config("coleta"))
    inicio, fim = (d.isoformat() for d in rede.periodo_lido())
    from faster_whisper import WhisperModel  # importado aqui: só o workflow instala
    modelo = WhisperModel(cfg["modelo"], device="cpu", compute_type="int8")
    comeco = time.monotonic()
    destino_publico = comum.RAIZ / "data" / "transcricoes" / "resumo.json"
    resumo = comum.carregar(destino_publico) if destino_publico.exists() else {"redes": {}}
    ok = 0
    for rede_id in opcoes.redes:
        todos = videos(privado, rede_id, inicio, fim)
        feitos = ja_transcritos(privado, rede_id)
        alvo = [v for v in todos if v["item_id"] not in feitos][: int(cfg.get(rede_id) or 0)]
        manifesto = rede.Manifesto("transcricao", {"rede": rede_id, "modelo": f"faster-whisper {cfg['modelo']} (int8, CPU)",
                                                   "idioma": "pt", "como_escolhe": (f"os {len(alvo)} endereços da planilha-semente JAMA ainda sem transcrição" if rede_id == "semente"
                                                                   else f"os {len(alvo)} vídeos do período com mais visualizações"),
                                                   "duracao_maxima_s": cfg["duracao_maxima_s"],
                                                   "ja_transcritos_antes": len(feitos)}, opcoes.run_id)
        linhas, falhas, parou = [], [], "lista_inteira"
        with tempfile.TemporaryDirectory() as tmp:
            for video in alvo:
                if (time.monotonic() - comeco) / 60 > opcoes.minutos:
                    parou = "tempo"
                    break
                if video.get("duracao_s") and video["duracao_s"] > cfg["duracao_maxima_s"]:
                    falhas.append({"item_id": video["item_id"], "motivo": "duração acima do limite"})
                    continue
                try:
                    arquivo = baixar_audio(video, pathlib.Path(tmp), int(cfg["duracao_maxima_s"]))
                    texto, idioma, duracao = transcrever(modelo, arquivo)
                    arquivo.unlink(missing_ok=True)
                except Exception as erro:
                    falhas.append({"item_id": video["item_id"], "motivo": rede.sem_chave(f"{type(erro).__name__}: {erro}")[:200]})
                    continue
                linhas.append({"rede": rede_id, "item_id": video["item_id"], "conta": video["conta"], "publicado_em": video["data"],
                               "duracao_s": duracao, "idioma": idioma, "texto": texto, "modelo": cfg["modelo"]})
                print(f"{rede_id} {len(linhas)}/{len(alvo)}: {duracao:.0f}s, {len(texto.split())} palavras", flush=True)
        carimbo = rede.carimbo(manifesto.dados["iniciado_em"])
        tabela = privado / "terceiros" / "transcricoes" / rede_id / f"transcricoes_{carimbo}.csv"
        tabela.parent.mkdir(parents=True, exist_ok=True)
        with tabela.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(linhas)
        manifesto.arquivo(tabela, privado, privado=True)
        motivos: dict[str, int] = {}
        for f in falhas:
            chave = f["motivo"].split(":")[0]
            motivos[chave] = motivos.get(chave, 0) + 1
        anterior = resumo["redes"].get(rede_id) or {}
        acumulado = len(feitos) + len(linhas)
        resumo["redes"][rede_id] = {"videos_no_periodo": len(todos), "tentados": len(alvo), "transcritos": len(linhas),
                                    "transcritos_no_total": acumulado,
                                    "palavras_no_total": ((anterior.get("palavras_no_total") or anterior.get("palavras") or 0) if feitos else 0)
                                    + sum(len(l["texto"].split()) for l in linhas),
                                    "falhas_por_motivo": motivos, "palavras": sum(len(l["texto"].split()) for l in linhas),
                                    "segundos": round(sum(l["duracao_s"] or 0 for l in linhas)), "obtido_em": manifesto.dados["iniciado_em"],
                                    "run_id": opcoes.run_id}
        manifesto.dados["consulta"]["falhas"] = falhas
        manifesto.dados.update({
            "universo": {"valor": len(todos), "fonte": "vídeos da rede já coletados no período lido (repositório privado)"},
            "transcritos_no_total": acumulado,
            "lido": len(alvo) if parou == "lista_inteira" else len(linhas) + len(falhas),
            "amostra": {"n": len(linhas), "como": "vídeos transcritos entre os mais vistos do período"},
            "parou_por": parou})
        print(f"gravado {manifesto.gravar().relative_to(comum.RAIZ)}: {rede_id}, {len(linhas)} de {len(alvo)} vídeos transcritos",
              flush=True)
        ok += 1 if linhas else 0
    resumo["nota"] = "Só contagens. As transcrições ficam no repositório privado e entram anonimizadas no corpus."
    comum.gravar(destino_publico, resumo)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
