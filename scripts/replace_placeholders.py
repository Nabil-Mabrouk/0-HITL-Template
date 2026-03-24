#!/usr/bin/env python3
"""
Script pour remplacer les placeholders dans le template.
À exécuter après la création d'un nouveau projet.
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List

# Mappings des placeholders avec leurs valeurs par défaut
# Ces valeurs seront remplacées par les vraies valeurs lors de l'initialisation
PLACEHOLDERS = {
    # Project identifiers
    "0-HITL": "{{PROJECT_NAME}}",
    "0-HITL": "{{PROJECT_NAME}}",  # variante sans espace
    "0hitl": "{{PROJECT_SLUG}}",
    "0-hitl.com": "{{PROJECT_DOMAIN}}",

    # Display names
    "Zero - Human In The Loop": "{{PROJECT_DISPLAY_NAME}}",
    "Zero Human In The Loop": "{{PROJECT_DISPLAY_NAME}}",

    # Emails and contact
    "ton@gmail.com": "{{DEFAULT_EMAIL}}",

    # Paths and URLs (à adapter selon le projet)
    "api.0-hitl.com": "api.{{PROJECT_DOMAIN}}",

    # Textes spécifiques (à rendre génériques)
    "L'automatisation intelligente arrive": "{{PROJECT_TAGLINE}}",

    # Branding colors (si spécifiées dans le code)
    "#000000": "{{PRIMARY_COLOR}}",  # Exemple, à vérifier
}

# Fichiers à ignorer (binaires, etc.)
IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.o', '.a', '.obj',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.zip', '.tar', '.gz', '.7z', '.rar',
    '.mp3', '.mp4', '.avi', '.mov',
    '.db', '.sqlite', '.sqlite3',
}

# Dossiers à ignorer
IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.next', '.nuxt', 'dist', 'build',
    '.idea', '.vscode', '__MACOSX',
}

def should_process_file(filepath: Path) -> bool:
    """Détermine si un fichier doit être traité."""
    # Ignorer les fichiers dans les dossiers à ignorer
    for part in filepath.parts:
        if part in IGNORE_DIRS:
            return False

    # Ignorer certaines extensions
    if filepath.suffix.lower() in IGNORE_EXTENSIONS:
        return False

    # Ignorer les fichiers trop grands (> 1MB)
    try:
        if filepath.stat().st_size > 1024 * 1024:
            return False
    except OSError:
        return False

    return True

def replace_in_file(filepath: Path, replacements: Dict[str, str]) -> bool:
    """Remplace les placeholders dans un fichier."""
    try:
        # Lire le contenu avec l'encodage approprié
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Appliquer les remplacements
        for old, new in replacements.items():
            content = content.replace(old, new)

        # Écrire seulement si des changements ont été faits
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  Erreur sur {filepath}: {e}")
        return False

def find_files(root_dir: Path) -> List[Path]:
    """Trouve tous les fichiers à traiter."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filtrer les dossiers à ignorer
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            filepath = Path(dirpath) / filename
            if should_process_file(filepath):
                files.append(filepath)
    return files

def main():
    parser = argparse.ArgumentParser(description="Remplacer les placeholders dans le template")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les changements sans les appliquer")
    parser.add_argument("--root", default=".", help="Racine du projet")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    print(f"Traitement du répertoire: {root_dir}")

    # Trouver tous les fichiers
    files = find_files(root_dir)
    print(f"Nombre de fichiers à traiter: {len(files)}")

    # Traiter chaque fichier
    changed_count = 0
    for i, filepath in enumerate(files, 1):
        if args.dry_run:
            # En mode dry-run, on vérifie juste si des remplacements seraient faits
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                would_change = False
                for old, new in PLACEHOLDERS.items():
                    if old in content:
                        print(f"  {filepath}: '{old}' → '{new}'")
                        would_change = True

                if would_change:
                    changed_count += 1
            except Exception as e:
                print(f"  Erreur sur {filepath}: {e}")
        else:
            # Appliquer réellement les remplacements
            if replace_in_file(filepath, PLACEHOLDERS):
                changed_count += 1

        if i % 100 == 0:
            print(f"  Traités: {i}/{len(files)}")

    print(f"\nTerminé. Fichiers modifiés: {changed_count}")

if __name__ == "__main__":
    main()