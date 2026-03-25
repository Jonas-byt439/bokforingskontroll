#!/bin/bash
# Publicera bokföringskontroll till GitHub → Streamlit Community Cloud
set -e

eval "$(/opt/homebrew/bin/brew shellenv)"

cd "$(dirname "$0")"

REPO_NAME="bokforingskontroll"
GITHUB_USER="Jonas-byt439"

echo "=== Publicerar Bokföringskontroll ==="
echo ""

# --- Git: initiera om det behövs ---
if [ ! -d ".git" ]; then
    echo "→ Initierar git-repo..."
    git init
    echo "__pycache__/" > .gitignore
    echo "*.pyc" >> .gitignore
    echo ".DS_Store" >> .gitignore
    git add -A
    git commit -m "Initial commit — Bokföringskontroll"
fi

# --- GitHub: skapa repo om det inte finns ---
if ! git remote | grep -q origin; then
    echo "→ Skapar GitHub-repo..."
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
else
    echo "→ Pushar ändringar till GitHub..."
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Uppdatering $(date '+%Y-%m-%d %H:%M')"
        git push origin main 2>/dev/null || git push origin master 2>/dev/null
        echo "✓ Nya ändringar pushade"
    else
        echo "✓ Inga nya ändringar att pusha"
    fi
fi

echo ""
echo "✓ GitHub: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "=== Deploy ==="
echo "Appen deployeras automatiskt via Streamlit Community Cloud."
echo "Om du inte kopplat repot ännu:"
echo "  1. Gå till https://share.streamlit.io"
echo "  2. Logga in med GitHub"
echo "  3. Välj repo: ${GITHUB_USER}/${REPO_NAME}"
echo "  4. Main file: Kontokontroll.py"
echo "  5. Klicka Deploy"
echo ""
echo "=== Klart! ==="
