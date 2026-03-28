#!/usr/bin/env python3
"""
setup_project.py — Script unique d'initialisation du projet.

Lit `project.json` à la racine du projet et remplace tous les placeholders
dans les fichiers sources. À lancer UNE SEULE FOIS après le clonage du template.

Usage:
    python scripts/setup_project.py                  # Applique project.json
    python scripts/setup_project.py --dry-run        # Prévisualise sans modifier
    python scripts/setup_project.py --json custom.json   # Fichier JSON alternatif
    python scripts/setup_project.py --root /path/to/project

Placeholders reconnus dans les sources (format {{KEY}}) :
    {{PROJECT_NAME}}         → Identifiant court (ex: my-app)
    {{PROJECT_DISPLAY_NAME}} → Nom affiché (ex: My App)
    {{PROJECT_SLUG}}         → Slug URL-safe (ex: myapp)
    {{PROJECT_DOMAIN}}       → Domaine (ex: myapp.com)
    {{DEFAULT_EMAIL}}        → Email de contact (ex: contact@myapp.com)
    {{PROJECT_TAGLINE}}      → Accroche (ex: The platform for X)
    {{PROJECT_DESCRIPTION}}  → Description longue
    {{PROJECT_AUTHOR}}       → Auteur / organisation
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# ── Valeurs template à remplacer (chaînes littérales dans les sources) ─────────
# Ces valeurs sont les occurences réelles du template d'origine.
# Elles seront remplacées par la valeur correspondante dans project.json.
TEMPLATE_LITERALS: dict[str, str] = {
    "0-HITL":                    "PROJECT_NAME",
    "0hitl":                     "PROJECT_SLUG",
    "0-hitl.com":                "PROJECT_DOMAIN",
    "api.0-hitl.com":            "PROJECT_DOMAIN",   # préfixé via remplacement de domaine
    "Zero - Human In The Loop":  "PROJECT_DISPLAY_NAME",
    "Zero Human In The Loop":    "PROJECT_DISPLAY_NAME",
    "ton@gmail.com":             "DEFAULT_EMAIL",
    "contact@example.com":       "DEFAULT_EMAIL",
}

# ── Extensions / dossiers ignorés ────────────────────────────────────────────
IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.o', '.a', '.obj',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.zip', '.tar', '.gz', '.7z', '.rar',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.db', '.sqlite', '.sqlite3', '.mmdb',
    '.lock',
}

IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.next', '.nuxt', 'dist', 'build',
    '.idea', '.vscode', '__MACOSX', '.claude',
}


def load_project_json(json_path: Path) -> dict[str, str]:
    """Charge et valide project.json."""
    if not json_path.exists():
        print(f"❌  Fichier introuvable : {json_path}")
        print("    Créez project.json à la racine du projet (voir project.json.example).")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    required = ["PROJECT_NAME", "PROJECT_DISPLAY_NAME", "PROJECT_SLUG",
                "PROJECT_DOMAIN", "DEFAULT_EMAIL"]
    missing = [k for k in required if k not in data or not data[k].strip()]
    if missing:
        print(f"❌  Clés manquantes ou vides dans {json_path} : {', '.join(missing)}")
        sys.exit(1)

    # Filtrer les commentaires (_comment, etc.)
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, str)}


def build_replacement_map(values: dict[str, str]) -> list[tuple[str, str]]:
    """
    Construit la liste ordonnée des remplacements (old → new).

    L'ordre compte : les chaînes longues passent avant les courtes pour éviter
    les remplacements partiels (ex: "0-hitl.com" avant "0-hitl").
    """
    replacements: list[tuple[str, str]] = []

    # 1. Placeholders {{KEY}} → valeur
    for key, value in values.items():
        replacements.append((f"{{{{{key}}}}}", value))

    # 2. Littéraux du template → valeur correspondante
    # Triés par longueur décroissante pour éviter les collisions
    for literal, key in sorted(TEMPLATE_LITERALS.items(), key=lambda x: -len(x[0])):
        if key in values:
            replacements.append((literal, values[key]))

    # Cas particulier : api.DOMAIN doit pointer vers api.PROJECT_DOMAIN
    domain = values.get("PROJECT_DOMAIN", "")
    if domain:
        replacements.append(("api.0-hitl.com", f"api.{domain}"))

    return replacements


def should_process(filepath: Path) -> bool:
    """Retourne True si le fichier doit être traité."""
    for part in filepath.parts:
        if part in IGNORE_DIRS:
            return False
    if filepath.suffix.lower() in IGNORE_EXTENSIONS:
        return False
    try:
        if filepath.stat().st_size > 1_000_000:   # > 1 Mo → skip
            return False
    except OSError:
        return False
    return True


def apply_replacements(filepath: Path,
                        replacements: list[tuple[str, str]],
                        dry_run: bool) -> bool:
    """Applique les remplacements dans un fichier. Retourne True si modifié."""
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            original = f.read()
    except OSError as e:
        print(f"  ⚠️  Lecture impossible : {filepath} ({e})")
        return False

    content = original
    for old, new in replacements:
        content = content.replace(old, new)

    if content == original:
        return False

    if dry_run:
        # Affiche quels tokens sont remplacés
        hits = [old for old, _ in replacements if old in original]
        print(f"  ~ {filepath.name}  ←  {', '.join(repr(h) for h in hits)}")
        return True

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        print(f"  ❌  Écriture impossible : {filepath} ({e})")
        return False


def walk_project(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if should_process(p):
                files.append(p)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialise le projet en remplaçant les placeholders via project.json"
    )
    parser.add_argument(
        "--json", default="project.json", metavar="FILE",
        help="Fichier JSON des valeurs (défaut : project.json)"
    )
    parser.add_argument(
        "--root", default=".", metavar="DIR",
        help="Racine du projet (défaut : répertoire courant)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Prévisualise les changements sans modifier aucun fichier"
    )
    args = parser.parse_args()

    root      = Path(args.root).resolve()
    json_path = Path(args.json) if Path(args.json).is_absolute() else root / args.json

    print("━" * 60)
    print("  setup_project.py — Initialisation du projet")
    print("━" * 60)

    # Charger les valeurs
    values = load_project_json(json_path)
    replacements = build_replacement_map(values)

    print("\n📋  Valeurs chargées :")
    for k, v in values.items():
        print(f"     {k:30s} → {v}")

    print(f"\n📂  Racine : {root}")
    if args.dry_run:
        print("🔍  Mode dry-run — aucune modification ne sera appliquée\n")

    # Scanner et traiter les fichiers
    files = walk_project(root)
    print(f"📄  {len(files)} fichiers à analyser...\n")

    changed = 0
    for fp in files:
        if apply_replacements(fp, replacements, dry_run=args.dry_run):
            changed += 1
            if not args.dry_run:
                print(f"  ✅  {fp.relative_to(root)}")

    print()
    print("━" * 60)
    if args.dry_run:
        print(f"  Fichiers qui seraient modifiés : {changed}")
        print("  Relancez sans --dry-run pour appliquer.")
    else:
        print(f"  ✅  Terminé — {changed} fichier(s) mis à jour.")
        print()
        print("  Prochaines étapes :")
        print("    1. cp .env.example .env  (puis remplir les valeurs)")
        print("    2. docker-compose -f docker-compose.dev.yml up --build")
        print("    3. docker-compose -f docker-compose.dev.yml run --rm migrate")
        print("    4. Ouvrir http://localhost:5173")
    print("━" * 60)


if __name__ == "__main__":
    main()
