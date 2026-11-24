#!/usr/bin/env bash
# Grava resultados de workflow no ramo main sem conflito com commits feitos durante a coleta.
# A cada tentativa: guarda os arquivos novos, parte do main mais recente, regenera data/estado.json a partir de
# todos os manifestos, insere a entrada de CHANGELOG já pronta, roda os testes e só então faz o commit e o push.
# Uso: scripts/gravar_no_main.sh "mensagem do commit" caminho/da/entrada.md pasta1 [pasta2 ...]
set -euo pipefail
mensagem="$1"; entrada="$2"; shift 2
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
copia="$(mktemp -d)"
for pasta in "$@"; do
  if [ -e "$pasta" ]; then mkdir -p "$copia/$(dirname "$pasta")"; cp -a "$pasta" "$copia/$pasta"; fi
done
for tentativa in 1 2 3 4; do
  git fetch -q origin main
  git reset -q --hard origin/main
  git clean -qfd -- "$@" 2>/dev/null || true
  for pasta in "$@"; do
    if [ -e "$copia/$pasta" ]; then mkdir -p "$(dirname "$pasta")"; cp -a "$copia/$pasta/." "$pasta/" 2>/dev/null || cp -a "$copia/$pasta" "$pasta"; fi
  done
  python scripts/build_estado.py
  python scripts/changelog_auto.py --inserir-de "$entrada"
  python -m unittest discover -s tests
  existentes=()
  for pasta in "$@"; do [ -e "$pasta" ] && existentes+=("$pasta"); done
  git add -A -- "${existentes[@]}" data/estado.json CHANGELOG.md
  if git diff --cached --quiet; then echo "nada mudou"; exit 0; fi
  git commit -q -m "$mensagem"
  if git push -q origin HEAD:main; then echo "gravado na tentativa $tentativa"; exit 0; fi
  sleep $((tentativa * 10))
done
echo "::error::não foi possível gravar no main depois de 4 tentativas"
exit 1
