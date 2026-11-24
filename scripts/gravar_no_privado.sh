#!/usr/bin/env bash
# Grava no repositório privado sem perder entrada de CHANGELOG quando outro workflow gravou ao mesmo tempo.
# Roda dentro do clone do privado. Conflito só no CHANGELOG.md é resolvido mantendo as duas entradas
# (scripts/mesclar_changelog.py); conflito em qualquer outro arquivo para o workflow com erro.
# Uso: gravar_no_privado.sh "mensagem do commit"
set -uo pipefail
mensagem="$1"
aqui="$(cd "$(dirname "$0")" && pwd)"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
if git diff --cached --quiet; then echo "nada mudou"; exit 0; fi
git commit -q -m "$mensagem"
for t in 1 2 3 4 5; do
  if git push -q origin HEAD:main; then echo "gravado no privado na tentativa $t"; exit 0; fi
  git fetch -q origin main
  if ! git rebase -q origin/main; then
    outros=$(git diff --name-only --diff-filter=U | grep -v '^CHANGELOG.md$' || true)
    if [ -n "$outros" ]; then echo "::error::conflito no privado fora do CHANGELOG: $outros"; git rebase --abort; exit 1; fi
    git show :2:CHANGELOG.md > "$RUNNER_TEMP/cl_remoto.md"
    git show :3:CHANGELOG.md > "$RUNNER_TEMP/cl_meu.md"
    python "$aqui/mesclar_changelog.py" "$RUNNER_TEMP/cl_remoto.md" "$RUNNER_TEMP/cl_meu.md" > CHANGELOG.md
    git add CHANGELOG.md
    GIT_EDITOR=true git rebase --continue || { git rebase --abort; exit 1; }
  fi
  sleep $((t * 5))
done
echo "::error::não foi possível gravar no privado"
exit 1
