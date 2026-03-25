#!/bin/bash
# Publicera bokföringskontroll till GitHub och Vercel
set -e

eval "$(/opt/homebrew/bin/brew shellenv)"

cd "$(dirname "$0")"

REPO_NAME="bokforingskontroll"

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
    echo "→ GitHub-repo finns redan"
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Uppdatering $(date '+%Y-%m-%d %H:%M')"
    fi
    git push origin main 2>/dev/null || git push origin master 2>/dev/null
fi

echo "✓ Pushat till GitHub"
echo ""

# --- Vercel: deploya ---
echo "→ Publicerar till Vercel..."
vercel --prod --yes 2>&1 | tail -5

echo ""
echo "=== Klart! ==="
