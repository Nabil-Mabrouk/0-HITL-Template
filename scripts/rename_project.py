#!/usr/bin/env python3
"""
Script de renommage pour personnaliser le template.
Remplace les placeholders par le nom du projet.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Placeholders à remplacer
PLACEHOLDERS = {
    "PROJECT_NAME": "",  # Remplacé par l'argument
    "PROJECT_SLUG": "",  # Version slugifiée
    "PROJECT_DESCRIPTION": "Plateforme Agentic AI",
    "PROJECT_AUTHOR": "Votre Nom",
    "PROJECT_EMAIL": "contact@example.com",
    "PROJECT_DOMAIN": "localhost",
    "PROJECT_VERSION": "1.0.0",
}

# Fichiers à ignorer
IGNORE_PATTERNS = [
    r'\.git/',
    r'\.env$',
    r'node_modules/',
    r'__pycache__/',
    r'\.pyc$',
    r'\.pyo$',
    r'\.pyd$',
    r'\.so$',
    r'\.dylib$',
    r'\.dll$',
    r'\.exe$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.png$',
    r'\.gif$',
    r'\.pdf$',
    r'\.zip$',
    r'\.tar$',
    r'\.gz$',
    r'\.mp3$',
    r'\.mp4$',
    r'\.wav$',
]

def slugify(text: str) -> str:
    """Convertit un texte en slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def should_ignore_file(filepath: str) -> bool:
    """Vérifie si un fichier doit être ignoré."""
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, filepath, re.IGNORECASE):
            return True
    return False

def replace_in_file(filepath: Path, replacements: List[Tuple[str, str]]) -> bool:
    """Remplace du texte dans un fichier."""
    try:
        # Lire le contenu
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Appliquer les remplacements
        for old, new in replacements:
            content = content.replace(old, new)

        # Écrire si changé
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except (UnicodeDecodeError, IOError) as e:
        print(f"  ⚠️  Impossible de lire {filepath}: {e}")
        return False

def rename_project_files(root_dir: Path, project_name: str, dry_run: bool = False):
    """Renomme les fichiers et contenu du projet."""

    # Préparer les valeurs
    project_slug = slugify(project_name)

    replacements = [
        ("{{PROJECT_NAME}}", project_name),
        ("{{PROJECT_SLUG}}", project_slug),
        ("{{PROJECT_SLUG_UPPER}}", project_slug.upper()),
        ("Template Agentic AI", project_name),
        ("template_agentic_ai", project_slug),
        ("template-agentic-ai", project_slug),
    ]

    print(f"🔧 Renommage du projet en: {project_name}")
    print(f"📁 Slug: {project_slug}")
    print(f"📂 Répertoire racine: {root_dir}")
    print()

    files_modified = 0

    # Parcourir les fichiers
    for filepath in root_dir.rglob('*'):
        if not filepath.is_file():
            continue

        rel_path = filepath.relative_to(root_dir)

        # Ignorer certains fichiers
        if should_ignore_file(str(rel_path)):
            continue

        # Remplacer dans le contenu
        if dry_run:
            print(f"📄 [DRY RUN] Examinerait: {rel_path}")
        else:
            try:
                if replace_in_file(filepath, replacements):
                    files_modified += 1
                    print(f"✅ Modifié: {rel_path}")
            except Exception as e:
                print(f"❌ Erreur avec {rel_path}: {e}")

        # Renommer le fichier si nécessaire
        old_name = filepath.name
        new_name = old_name

        for old, new in replacements:
            if old in new_name:
                new_name = new_name.replace(old, new)

        if new_name != old_name:
            new_path = filepath.parent / new_name
            if dry_run:
                print(f"📝 [DRY RUN] Renommerait: {rel_path} -> {new_path.name}")
            else:
                try:
                    filepath.rename(new_path)
                    print(f"📝 Renommé: {rel_path} -> {new_path.name}")
                except Exception as e:
                    print(f"❌ Erreur renommage {rel_path}: {e}")

    print()
    print(f"📊 Résumé:")
    print(f"   Fichiers modifiés: {files_modified}")
    print(f"   Nom du projet: {project_name}")
    print(f"   Slug du projet: {project_slug}")

    if dry_run:
        print("\n⚠️  Mode test activé - Aucune modification réelle effectuée.")
        print("   Pour appliquer les changements, retirez l'option --dry-run.")

def main():
    parser = argparse.ArgumentParser(description='Renomme le template pour un nouveau projet.')
    parser.add_argument('project_name', help='Nom du nouveau projet')
    parser.add_argument('--dry-run', action='store_true', help='Mode test sans modifications')
    parser.add_argument('--root-dir', default='.', help='Répertoire racine du template')

    args = parser.parse_args()

    root_dir = Path(args.root_dir).resolve()

    if not root_dir.exists():
        print(f"❌ Répertoire non trouvé: {root_dir}")
        sys.exit(1)

    rename_project_files(root_dir, args.project_name, args.dry_run)

if __name__ == '__main__':
    main()