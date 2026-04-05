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

def run_command(command: str, description: str, exit_on_error: bool = True) -> bool:
    """Exécute une commande système. Retourne True si succès."""
    console.print(f"[bold blue]→ {description}...[/bold blue]")
    try:
        subprocess.run(command, shell=True, check=True, cwd=ROOT, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Erreur lors de {description}[/bold red]")
        if exit_on_error:
            console.print("[dim]Le script s'arrête ici pour éviter des incohérences.[/dim]")
            raise typer.Exit(code=1)
        return False

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

def update_env(env_path: Path, values: dict):
    """Met à jour ou ajoute des variables dans le fichier .env."""
    if not env_path.exists():
        return
        
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    keys_handled = set()
    
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                new_lines.append(f"{key}={values[key]}\n")
                keys_handled.add(key)
                continue
        new_lines.append(line)
    
    for key, value in values.items():
        if key not in keys_handled:
            new_lines.append(f"{key}={value}\n")
            
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

@app.command()
def init():
    """Initialise le projet (Première utilisation)"""
    console.print(Panel.fit(
        "[bold cyan]🚀 Configuration du projet 0-HITL[/bold cyan]\n"
        "[dim]Ce script va configurer votre environnement complet en quelques étapes.[/dim]",
        border_style="cyan"
    ))

    # 0. Charger les valeurs par défaut
    defaults = {"PROJECT_NAME": "my-app", "PROJECT_DISPLAY_NAME": "My Awesome App", "PROJECT_DOMAIN": "myapp.com", "DEFAULT_EMAIL": "contact@myapp.com"}
    if PROJECT_JSON.exists():
        try:
            with open(PROJECT_JSON, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception: pass

    # 1. Identification
    console.print("\n[bold]📦 Étape 1 : Identification[/bold]")
    name = Prompt.ask("Nom technique du projet (slug)", default=defaults["PROJECT_NAME"])
    display_name = Prompt.ask("Nom affiché", default=defaults["PROJECT_DISPLAY_NAME"])
    domain = Prompt.ask("Domaine", default=defaults["PROJECT_DOMAIN"])
    contact_email = Prompt.ask("Email de contact", default=defaults.get("DEFAULT_EMAIL", f"contact@{domain}"))

    values = {"PROJECT_NAME": name, "PROJECT_DISPLAY_NAME": display_name, "PROJECT_SLUG": name.replace("-", "").lower(), "PROJECT_DOMAIN": domain, "DEFAULT_EMAIL": contact_email}
    with open(PROJECT_JSON, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=4)

    if Confirm.ask("Voulez-vous appliquer les remplacements de placeholders dans les fichiers ?", default=True):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description="Remplacement des placeholders...", total=None)
            count = apply_replacements(values)
        console.print(f"[green]✅ {count} fichiers mis à jour.[/green]")

    # 2. Environnement (.env)
    console.print("\n[bold]⚙️ Étape 2 : Environnement (.env)[/bold]")
    if not ENV_FILE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
    
    env_updates = {"PROJECT_NAME": values["PROJECT_SLUG"], "VITE_API_URL": f"https://api.{domain}", "POSTGRES_DB": values["PROJECT_SLUG"]}
    
    # -- Database --
    console.print("\n[blue]🗄️ Base de données PostgreSQL[/blue]")
    env_updates["POSTGRES_USER"] = Prompt.ask("Utilisateur DB", default=values["PROJECT_SLUG"])
    env_updates["POSTGRES_PASSWORD"] = Prompt.ask("Mot de passe DB (vide = généré)", default="", show_default=False)
    if not env_updates["POSTGRES_PASSWORD"]:
        env_updates["POSTGRES_PASSWORD"] = generate_secret(16)
        console.print(f"[dim]Généré : {env_updates['POSTGRES_PASSWORD']}[/dim]")

    # -- Secrets --
    console.print("\n[blue]🔐 Sécurité & Secrets[/blue]")
    env_updates["SECRET_KEY"] = Prompt.ask("SECRET_KEY JWT (vide = généré)", default="", show_default=False)
    if not env_updates["SECRET_KEY"]:
        env_updates["SECRET_KEY"] = generate_secret(32)
        console.print(f"[dim]Généré : {env_updates['SECRET_KEY']}[/dim]")
    env_updates["JWT_SECRET"] = env_updates["SECRET_KEY"]
    
    # -- Auth Channels --
    console.print("\n[blue]🚪 Canaux d'authentification[/blue]")
    env_updates["AUTH_CHANNEL_WAITLIST"] = "true" if Confirm.ask("Activer la Waitlist ?", default=True) else "false"
    env_updates["AUTH_CHANNEL_DIRECT"] = "true" if Confirm.ask("Activer l'inscription directe ?", default=False) else "false"
    env_updates["AUTH_CHANNEL_ONBOARDING"] = "true" if Confirm.ask("Activer l'Onboarding ?", default=False) else "false"
    
    # -- Email --
    console.print("\n[blue]📧 Configuration Email[/blue]")
    env_updates["SMTP_USER"] = Prompt.ask("SMTP User (Gmail/etc)", default=contact_email)
    env_updates["EMAIL_FROM"] = env_updates["SMTP_USER"]
    env_updates["EMAIL_FROM_NAME"] = display_name
    if Confirm.ask("Voulez-vous configurer le mot de passe SMTP maintenant ?", default=False):
        env_updates["SMTP_PASSWORD"] = Prompt.ask("SMTP App Password", password=True)

    # -- Monetization --
    console.print("\n[blue]💰 Monétisation[/blue]")
    env_updates["MONETIZATION_SHOP"] = "true" if Confirm.ask("Activer la Boutique ?", default=False) else "false"
    env_updates["MONETIZATION_SUBSCRIPTION"] = "true" if Confirm.ask("Activer les Abonnements ?", default=False) else "false"

    # -- Initial Admin --
    console.print("\n[blue]👤 Administrateur Initial[/blue]")
    env_updates["ADMIN_EMAIL"] = Prompt.ask("Email de l'admin", default=contact_email)
    env_updates["ADMIN_PASSWORD"] = Prompt.ask("Mot de passe admin", default="AdminSecure123!")
    env_updates["ADMIN_FULL_NAME"] = Prompt.ask("Nom complet admin", default="Admin")

    update_env(ENV_FILE, env_updates)
    console.print("[green]✅ Fichier .env configuré.[/green]")

    # 3. Git
    console.print("\n[bold]🌿 Étape 3 : Git[/bold]")
    git_dir = ROOT / ".git"
    if Confirm.ask("Voulez-vous configurer le dépôt Git ?", default=True):
        if git_dir.exists() and Confirm.ask("[yellow]⚠️  Dépôt Git existant. Réinitialiser ?[/yellow]", default=False):
            shutil.rmtree(git_dir, onerror=handle_remove_readonly)
        
        if not git_dir.exists():
            run_command("git init", "Initialisation de Git")
        
        repo_url = Prompt.ask("URL du dépôt distant (optionnel)", default="")
        if repo_url:
            try:
                remotes = subprocess.check_output("git remote", shell=True, cwd=ROOT).decode().split()
                if "origin" in remotes:
                    run_command(f"git remote set-url origin {repo_url}", "Mise à jour du remote")
                else:
                    run_command(f"git remote add origin {repo_url}", "Ajout du remote")
            except Exception:
                run_command(f"git remote add origin {repo_url}", "Ajout du remote")
        
        run_command("git add .", "Staging")
        try:
            status = subprocess.check_output("git status --porcelain", shell=True, cwd=ROOT).decode()
            if status:
                run_command(f'git commit -m "chore: initial project setup from {name} template"', "Premier commit")
        except Exception: pass
        
        if repo_url and Confirm.ask("Voulez-vous pousser le code maintenant ?", default=True):
            branch = Prompt.ask("Branche", default="main")
            run_command(f"git branch -M {branch}", f"Branche {branch}")
            success = run_command(f"git push -u origin {branch}", "Push vers origin", exit_on_error=False)
            
            if not success:
                console.print("[yellow]⚠️  Le push a échoué (dépôt non vide ?).[/yellow]")
                if Confirm.ask("Voulez-vous tenter un FORCE PUSH ?", default=False):
                    run_command(f"git push -f origin {branch}", "Force push")

    # 4. Docker
    console.print("\n[bold]🐳 Étape 4 : Docker[/bold]")
    if Confirm.ask("Voulez-vous lancer le build Docker maintenant ?", default=False):
        run_command("docker compose -f docker-compose.dev.yml up --build -d", "Docker Up")
        console.print("[green]✅ Docker lancé ! http://localhost:5173[/green]")

    console.print("\n[bold green]✨ Initialisation terminée ! ✨[/bold green]")

@app.command()
def dev():
    """Lance l'environnement de développement (Docker)"""
    run_command("docker compose -f docker-compose.dev.yml up", "Docker Up")

@app.command()
def migrate():
    """Applique les migrations de base de données"""
    run_command("docker compose -f docker-compose.dev.yml exec backend alembic upgrade head", "Migrations")

@app.command()
def stop():
    """Arrête les conteneurs Docker"""
    run_command("docker compose -f docker-compose.dev.yml down", "Docker Down")

if __name__ == "__main__":
    app()
