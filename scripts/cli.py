#!/usr/bin/env python3
import os
import json
import secrets
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# --- Configuration ---
ROOT = Path(__file__).parent.parent.resolve()
PROJECT_JSON = ROOT / "project.json"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

# Logic for replacements (reused from setup_project.py)
TEMPLATE_LITERALS = {
    "0-HITL": "PROJECT_NAME",
    "0hitl": "PROJECT_SLUG",
    "0-hitl.com": "PROJECT_DOMAIN",
    "api.0-hitl.com": "PROJECT_DOMAIN",
    "Zero - Human In The Loop": "PROJECT_DISPLAY_NAME",
    "Zero Human In The Loop": "PROJECT_DISPLAY_NAME",
    "ton@gmail.com": "DEFAULT_EMAIL",
    "contact@example.com": "DEFAULT_EMAIL",
}

IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.o', '.a', '.obj', '.png', '.jpg', '.jpeg', '.gif',
    '.bmp', '.ico', '.webp', '.svg', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.zip', '.tar', '.gz', '.7z', '.rar', '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.db', '.sqlite', '.sqlite3', '.mmdb', '.lock',
}

IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules', '.next',
    '.nuxt', 'dist', 'build', '.idea', '.vscode', '__MACOSX', '.claude',
}

app = typer.Typer(help="CLI de gestion pour le template 0-HITL")
console = Console()

def generate_secret(length: int = 32) -> str:
    return secrets.token_hex(length)

def run_command(command: str, description: str):
    console.print(f"[bold blue]→ {description}...[/bold blue]")
    try:
        subprocess.run(command, shell=True, check=True, cwd=ROOT)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Erreur lors de l'exécution : {e}[/bold red]")
        raise typer.Exit(code=1)

def apply_replacements(values: dict):
    replacements = []
    for key, value in values.items():
        replacements.append((f"{{{{{key}}}}}", value))
    
    for literal, key in sorted(TEMPLATE_LITERALS.items(), key=lambda x: -len(x[0])):
        if key in values:
            replacements.append((literal, values[key]))

    domain = values.get("PROJECT_DOMAIN", "")
    if domain:
        replacements.append(("api.0-hitl.com", f"api.{domain}"))

    count = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            fp = Path(dirpath) / name
            if fp.suffix.lower() in IGNORE_EXTENSIONS or fp.stat().st_size > 1_000_000:
                continue
            
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    original = f.read()
                
                content = original
                for old, new in replacements:
                    content = content.replace(old, new)
                
                if content != original:
                    with open(fp, "w", encoding="utf-8") as f:
                        f.write(content)
                    count += 1
            except Exception:
                continue
    return count

def handle_remove_readonly(func, path, excinfo):
    """Handler pour shutil.rmtree qui gère les fichiers en lecture seule (Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

@app.command()
def init():
    """Initialise le projet (Première utilisation)"""
    console.print(Panel.fit(
        "[bold cyan]🚀 Initialisation du projet 0-HITL[/bold cyan]\n"
        "[dim]Ce script va configurer votre nouveau projet en quelques étapes.[/dim]",
        border_style="cyan"
    ))

    # 1. Collecte des informations
    name = Prompt.ask("Nom technique du projet (slug, ex: my-app)", default="my-app")
    display_name = Prompt.ask("Nom affiché (ex: My Awesome App)", default="My Awesome App")
    domain = Prompt.ask("Domaine (ex: myapp.com)", default="myapp.com")
    email = Prompt.ask("Email par défaut", default=f"contact@{domain}")

    values = {
        "PROJECT_NAME": name,
        "PROJECT_DISPLAY_NAME": display_name,
        "PROJECT_SLUG": name.replace("-", ""),
        "PROJECT_DOMAIN": domain,
        "DEFAULT_EMAIL": email
    }

    # 2. Sauvegarde project.json
    with open(PROJECT_JSON, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=4)
    console.print("[green]✅ project.json mis à jour.[/green]")

    # 3. Application des remplacements
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Remplacement des placeholders...", total=None)
        count = apply_replacements(values)
    console.print(f"[green]✅ {count} fichiers mis à jour avec vos informations.[/green]")

    # 4. Configuration du .env
    if not ENV_FILE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        
        # Génération des secrets
        jwt_secret = generate_secret()
        db_password = generate_secret(16)
        
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("SECRET_KEY="):
                    f.write(f"SECRET_KEY={jwt_secret}\n")
                elif line.startswith("POSTGRES_PASSWORD="):
                    f.write(f"POSTGRES_PASSWORD={db_password}\n")
                elif line.startswith("JWT_SECRET="):
                    f.write(f"JWT_SECRET={jwt_secret}\n")
                else:
                    f.write(line)
        console.print("[green]✅ Fichier .env créé avec des secrets sécurisés.[/green]")
    else:
        console.print("[yellow]⚠️  Le fichier .env existe déjà, ignoré.[/yellow]")

    # 5. Git (Optionnel)
    if Confirm.ask("Voulez-vous réinitialiser le dépôt Git pour ce projet ?", default=True):
        if (ROOT / ".git").exists():
            shutil.rmtree(ROOT / ".git", onerror=handle_remove_readonly)
        run_command("git init", "Initialisation de Git")
        run_command("git add .", "Staging des fichiers")
        run_command(f'git commit -m "chore: initial project setup from {name} template"', "Premier commit")
        console.print("[green]✅ Dépôt Git prêt.[/green]")

    # 6. Docker (Optionnel)
    if Confirm.ask("Voulez-vous lancer le build Docker maintenant ?", default=False):
        run_command("docker compose -f docker-compose.dev.yml up --build -d", "Build et démarrage Docker")
        console.print("[green]✅ Environnement Docker lancé ![/green]")
        console.print("[bold cyan]Accédez à votre application : http://localhost:5173[/bold cyan]")

    console.print("\n[bold green]✨ Initialisation terminée avec succès ! ✨[/bold green]")

@app.command()
def dev():
    """Lance l'environnement de développement (Docker)"""
    run_command("docker compose -f docker-compose.dev.yml up", "Lancement de l'environnement dev")

@app.command()
def migrate():
    """Applique les migrations de base de données"""
    run_command("docker compose -f docker-compose.dev.yml exec backend alembic upgrade head", "Migration de la base de données")

@app.command()
def stop():
    """Arrête les conteneurs Docker"""
    run_command("docker compose -f docker-compose.dev.yml down", "Arrêt des conteneurs")

if __name__ == "__main__":
    app()
