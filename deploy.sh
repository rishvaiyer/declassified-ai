#!/usr/bin/env bash
# One-shot: create the GitHub repo, push everything, and turn on GitHub Pages.
# Requires the GitHub CLI (`gh`) logged in:  gh auth login
# Run it from inside this folder:  bash deploy.sh
set -e

REPO="declassified-ai"
DESC="Declassified AI — an interactive dossier of leaked system prompts from 25 AI companies."

command -v gh >/dev/null || { echo "❌ Need the GitHub CLI. Install: https://cli.github.com  then: gh auth login"; exit 1; }

git init -q
git add .
git commit -q -m "Declassified AI: interactive dossier of leaked AI system prompts"
git branch -M main

# create the repo under your account and push
gh repo create "$REPO" --public --source=. --remote=origin --description "$DESC" --push

LOGIN=$(gh api user -q .login)

# enable GitHub Pages from main / root
gh api -X POST "repos/$LOGIN/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/' >/dev/null 2>&1 \
  || gh api -X PUT "repos/$LOGIN/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/' >/dev/null 2>&1 \
  || echo "ℹ️  Couldn't auto-enable Pages — flip it on at: https://github.com/$LOGIN/$REPO/settings/pages (Source: main / root)"

echo ""
echo "✅ Repo:  https://github.com/$LOGIN/$REPO"
echo "🌐 Site (live in ~1 min):  https://$LOGIN.github.io/$REPO/"
