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
from rich.table import Table

# --- Configuration ---
ROOT = Path(__file__).parent.parent.resolve()
PROJECT_JSON = ROOT / "project.json"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"
STYLE_PROMPT_TEMPLATE = ROOT / "frontend_prompt.md"
STYLE_PROMPT_OUTPUT = ROOT / "STYLING_PROMPT.md"
TUTORIAL_PROMPT_OUTPUT = ROOT / "TUTORIAL_PROMPT.md"

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

app = typer.Typer(
    help="CLI de gestion pour le template 0-HITL",
    no_args_is_help=True,
    add_completion=False
)
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
            except Exception: continue
    return count

def handle_remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def update_env(env_path: Path, values: dict):
    if not env_path.exists(): return
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines, keys_handled = [], set()
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

@app.command(name="help")
def show_help():
    """Affiche la liste des commandes disponibles"""
    console.print(Panel.fit("[bold cyan]🛠️ Commandes disponibles pour 0-HITL[/bold cyan]", border_style="cyan"))
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Commande", style="bold yellow")
    table.add_column("Description")
    table.add_row("init", "Initialisation complète (Placeholders, .env, Git, Docker)")
    table.add_row("style", "Génère un prompt de design personnalisé (Frontend)")
    table.add_row("tutorial", "Génère un prompt pour créer un cours complet de 10 leçons")
    table.add_row("dev", "Lance l'environnement de développement Docker")
    table.add_row("migrate", "Applique les migrations de base de données")
    table.add_row("clean", "NETTOYAGE COMPLET (Supprime volumes/données)")
    table.add_row("stop", "Arrête les conteneurs")
    console.print(table)

@app.command()
def init():
    """Initialise le projet (Première utilisation)"""
    console.print(Panel.fit("[bold cyan]🚀 Configuration du projet 0-HITL[/bold cyan]", border_style="cyan"))
    defaults = {"PROJECT_NAME": "my-app", "PROJECT_DISPLAY_NAME": "My Awesome App", "PROJECT_DOMAIN": "myapp.com", "DEFAULT_EMAIL": "contact@myapp.com"}
    if PROJECT_JSON.exists():
        try:
            with open(PROJECT_JSON, "r", encoding="utf-8") as f: defaults.update(json.load(f))
        except Exception: pass

    name = Prompt.ask("Nom technique (slug)", default=defaults["PROJECT_NAME"])
    display_name = Prompt.ask("Nom affiché", default=defaults["PROJECT_DISPLAY_NAME"])
    domain = Prompt.ask("Domaine", default=defaults["PROJECT_DOMAIN"])
    contact_email = Prompt.ask("Email de contact", default=defaults.get("DEFAULT_EMAIL", f"contact@{domain}"))

    values = {"PROJECT_NAME": name, "PROJECT_DISPLAY_NAME": display_name, "PROJECT_SLUG": name.replace("-", "").lower(), "PROJECT_DOMAIN": domain, "DEFAULT_EMAIL": contact_email}
    with open(PROJECT_JSON, "w", encoding="utf-8") as f: json.dump(values, f, indent=4)

    if Confirm.ask("Appliquer les remplacements ?", default=True):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description="Traitement...", total=None)
            count = apply_replacements(values)
        console.print(f"[green]✅ {count} fichiers mis à jour.[/green]")

    if not ENV_FILE.exists(): shutil.copy(ENV_EXAMPLE, ENV_FILE)
    
    env_updates = {"PROJECT_NAME": values["PROJECT_SLUG"], "COMPOSE_PROJECT_NAME": values["PROJECT_SLUG"], "VITE_API_URL": f"https://api.{domain}", "POSTGRES_DB": values["PROJECT_SLUG"]}
    env_updates["POSTGRES_USER"] = Prompt.ask("Utilisateur DB", default=values["PROJECT_SLUG"])
    env_updates["POSTGRES_PASSWORD"] = Prompt.ask("MDP DB (vide=généré)", default="", show_default=False) or generate_secret(16)
    if env_updates["POSTGRES_PASSWORD"]: console.print(f"[dim]Généré : {env_updates['POSTGRES_PASSWORD']}[/dim]")
    env_updates["SECRET_KEY"] = Prompt.ask("SECRET_KEY JWT (vide=généré)", default="", show_default=False) or generate_secret(32)
    if env_updates["SECRET_KEY"]: console.print(f"[dim]Généré : {env_updates['SECRET_KEY']}[/dim]")
    env_updates["JWT_SECRET"] = env_updates["SECRET_KEY"]
    
    env_updates["AUTH_CHANNEL_WAITLIST"] = "true" if Confirm.ask("Waitlist ?", default=True) else "false"
    env_updates["AUTH_CHANNEL_DIRECT"] = "true" if Confirm.ask("Direct Reg ?", default=False) else "false"
    env_updates["AUTH_CHANNEL_ONBOARDING"] = "true" if Confirm.ask("Onboarding ?", default=False) else "false"
    
    env_updates["SMTP_USER"] = Prompt.ask("SMTP User", default=contact_email)
    env_updates["EMAIL_FROM"] = env_updates["SMTP_USER"]
    env_updates["EMAIL_FROM_NAME"] = display_name
    if Confirm.ask("Config SMTP Password ?", default=False): env_updates["SMTP_PASSWORD"] = Prompt.ask("Password", password=True)

    env_updates["MONETIZATION_SHOP"] = "true" if Confirm.ask("Shop ?", default=False) else "false"
    env_updates["MONETIZATION_SUBSCRIPTION"] = "true" if Confirm.ask("Sub ?", default=False) else "false"

    env_updates["ADMIN_EMAIL"] = Prompt.ask("Admin Email", default=contact_email)
    env_updates["ADMIN_PASSWORD"] = Prompt.ask("Admin MDP", default="AdminSecure123!")
    env_updates["ADMIN_FULL_NAME"] = Prompt.ask("Admin Name", default="Admin")

    update_env(ENV_FILE, env_updates)
    console.print("[green]✅ .env configuré.[/green]")

    git_dir = ROOT / ".git"
    if Confirm.ask("Config Git ?", default=True):
        if git_dir.exists() and Confirm.ask("Reset Git ?", default=False): shutil.rmtree(git_dir, onerror=handle_remove_readonly)
        if not git_dir.exists(): run_command("git init", "Git Init")
        repo_url = Prompt.ask("Repo URL (opt)", default="")
        if repo_url:
            try:
                remotes = subprocess.check_output("git remote", shell=True, cwd=ROOT).decode().split()
                cmd = f"git remote set-url origin {repo_url}" if "origin" in remotes else f"git remote add origin {repo_url}"
                run_command(cmd, "Config Remote")
            except Exception: run_command(f"git remote add origin {repo_url}", "Add Remote")
        run_command("git add .", "Staging")
        try:
            if subprocess.check_output("git status --porcelain", shell=True, cwd=ROOT).decode():
                run_command(f'git commit -m "chore: init from {name}"', "Commit")
        except Exception: pass
        if repo_url and Confirm.ask("Push ?", default=True):
            branch = Prompt.ask("Branch", default="main")
            run_command(f"git branch -M {branch}", f"Branch {branch}")
            if not run_command(f"git push -u origin {branch}", "Push", exit_on_error=False):
                if Confirm.ask("Force Push ?", default=False): run_command(f"git push -f origin {branch}", "Force Push")

    if Confirm.ask("Lancer Docker ?", default=False):
        if Confirm.ask("Effacer les données ?", default=False): run_command("docker compose -f docker-compose.dev.yml down -v", "Clean")
        run_command("docker compose -f docker-compose.dev.yml build", "Docker Build")
        run_command("docker-compose -f docker-compose.dev.yml run --rm migrate alembic revision --autogenerate ", "Docker Migrate", exit_on_error=False)
        run_command("docker compose -f docker-compose.dev.yml up", "Docker Up")
        console.print("[green]✅ http://localhost:5173[/green]")

@app.command()
def style():
    """Génère un prompt de design pur pour Gemini/Claude"""
    console.print(Panel.fit("[bold cyan]🎨 Prompt de Style[/bold cyan]", border_style="cyan"))
    project_name = "0-HITL"
    if PROJECT_JSON.exists():
        with open(PROJECT_JSON, "r") as f: project_name = json.load(f).get("PROJECT_DISPLAY_NAME", "0-HITL")

    domain = Prompt.ask("Domaine métier")
    audience = Prompt.ask("Public cible")
    vibe = Prompt.ask("Ambiance (ex: Minimal & Luxe)")
    color = Prompt.ask("Couleur dominante", default="Choisir pour moi")
    preset = Prompt.ask("Preset (minimal, vibrant, glass, brutal, editorial)", default="minimal")
    features = Prompt.ask("3 Features clés")
    lang = Prompt.ask("Langue", default="Français")

    desc = f"Application: {project_name}\nDomaine: {domain}\nPublic: {audience}\nAmbiance: {vibe}\nPalette: {color} (Preset: {preset})\nFeatures: {features}\nLangue: {lang}"

    if not STYLE_PROMPT_TEMPLATE.exists(): return
    with open(STYLE_PROMPT_TEMPLATE, "r", encoding="utf-8") as f: content = f.read()

    # Extraction du prompt pur (après le marqueur)
    marker = "*(Tout ce qui suit est destiné à l'agent — copier-coller tel quel)*"
    if marker in content:
        pure_prompt = content.split(marker)[1].strip()
    else:
        pure_prompt = content

    final_prompt = pure_prompt.replace("[REMPLACER CE BLOC PAR LA DESCRIPTION DE VOTRE APPLICATION]", desc)
    with open(STYLE_PROMPT_OUTPUT, "w", encoding="utf-8") as f: f.write(final_prompt)

    console.print(f"[green]✅ Prompt généré : {STYLE_PROMPT_OUTPUT}[/green]")
    if Confirm.ask("🚀 Envoyer à Gemini ?", default=True):
        subprocess.run(f'gemini -p "{final_prompt.replace('"', "'")}"', shell=True, cwd=ROOT)

@app.command()
def tutorial():
    """Génère un prompt pour créer un tutoriel complet (10 leçons)"""
    console.print(Panel.fit("[bold cyan]📚 Générateur de Tutoriel[/bold cyan]", border_style="cyan"))
    subject = Prompt.ask("Sujet du tutoriel")
    level = Prompt.ask("Niveau (Débutant, Avancé...)", default="Débutant")
    goals = Prompt.ask("Objectif principal du cours")
    lang = Prompt.ask("Langue", default="Français")

    prompt = f"""Tu es un expert pédagogique. Crée un tutoriel complet sur '{subject}' pour un niveau '{level}'.
Objectif : {goals}
Langue : {lang}

Le tutoriel doit être structuré pour un import automatique dans mon application. 
Fournis-moi le contenu de 11 fichiers JSON (1 pour le tutoriel, 10 pour les leçons) en respectant exactement ces schémas :

1. Fichier 'tutorial.json' :
{{
  "title": "Titre complet",
  "slug": "{subject.lower().replace(' ', '-')}",
  "description": "Description détaillée",
  "is_published": true,
  "is_premium": false
}}

2. 10 Fichiers dans 'lessons/*.json' (ex: lessons/01-intro.json) :
{{
  "title": "Titre de la leçon",
  "slug": "slug-unique",
  "content": "Contenu riche au format Markdown (utilise des titres, listes, code blocks)",
  "order": 1,
  "is_published": true
}}

Instructions importantes :
- Le contenu des leçons doit être très détaillé et professionnel.
- Utilise un ton engageant.
- Assure-toi que les slugs sont uniques.
- Réponds UNIQUEMENT avec le code nécessaire pour créer ces fichiers (ou un script bash/python pour les générer).
"""
    with open(TUTORIAL_PROMPT_OUTPUT, "w", encoding="utf-8") as f: f.write(prompt)
    console.print(f"[green]✅ Prompt tutoriel généré : {TUTORIAL_PROMPT_OUTPUT}[/green]")
    if Confirm.ask("🚀 Envoyer à Gemini ?", default=True):
        subprocess.run(f'gemini -p "{prompt.replace('"', "'")}"', shell=True, cwd=ROOT)

@app.command()
def up(): run_command("docker compose -f docker-compose.dev.yml up", "Dev")
@app.command()
def build(): run_command("docker compose -f docker-compose.dev.yml build", "Docker Build")
@app.command()
def migrate(): run_command("docker-compose -f docker-compose.dev.yml run --rm migrate alembic revision --autogenerate ", "Docker Migrate", exit_on_error=False)
@app.command()
def down(): run_command("docker compose -f docker-compose.dev.yml down", "Docker Down")
@app.command()
def clean():
    if Confirm.ask("Effacer les données ?", default=False): run_command("docker compose -f docker-compose.dev.yml down -v", "Clean")

if __name__ == "__main__": app()
