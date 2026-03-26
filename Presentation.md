# Instructions pour le Template Agentic AI

## 📋 Aperçu

Ce template est basé sur Z-HITL et étendu avec une architecture complète pour les services agentic IA. Il comprend:

1. **Backend FastAPI** complet avec authentification, base de données, etc.
2. **Frontend React/TypeScript** avec dashboard utilisateur
3. **Système modulaire de services agentic IA** avec orchestration d'agents
4. **Scripts de personnalisation** pour nouveaux projets

## 🚀 Utilisation Rapide

### 1. Cloner et renommer
```bash
# Copier le template
cp -r template-agentic-ai mon-nouveau-projet
cd mon-nouveau-projet

# Renommer le projet
python scripts/rename_project.py "Nom de Mon Projet"
```

### 2. Configurer l'environnement
```bash
cp .env.example .env
# Éditer .env avec vos clés API, etc.
```

### 3. Lancer avec Docker
```bash
docker-compose up -d
```

## 🏗️ Architecture des Services Agentic IA

### Structure Backend
```
backend/app/agents/
├── core/           # Composants partagés
├── services/       # Services modulaires
├── tools/         # Outils disponibles
└── service_registry.py
```

### Structure Frontend
```
frontend/src/
├── agent-dashboard/  # Dashboard principal
├── agent-services/   # Composants par service
└── agent-commons/    # Composants partagés
```

## 🔧 Ajouter un Nouveau Service

### 1. Backend
```bash
# Créer la structure
mkdir -p backend/app/agents/services/mon_service
cp backend/app/agents/services/template_service/* backend/app/agents/services/mon_service/

# Éditer config.yaml dans le nouveau répertoire
```

### 2. Frontend
```bash
# Créer le composant
cp -r frontend/src/agent-services/template frontend/src/agent-services/MonService

# Enregistrer dans frontend/src/agent-services/ServiceLoader.tsx
```

### 3. Configuration
```yaml
# config/agent_services.yaml
services:
  mon_service:
    enabled: true
    name: "Mon Service"
    description: "Description du service"
    icon: "activity"
    category: "custom"
```

## 📁 Fichiers Importants

- `scripts/rename_project.py` - Renomme le projet
- `config/agent_services.yaml` - Configuration des services
- `backend/app/agents/service_registry.py` - Registre des services
- `frontend/src/agent-dashboard/` - Dashboard utilisateur

## 🔖 Placeholders du Template

Le template utilise des marqueurs `{{PLACEHOLDER}}` qui sont remplacés par vos valeurs réelles lors de l'initialisation du projet. Voici la liste complète :

| Placeholder | Description | Exemple |
|---|---|---|
| `{{PROJECT_NAME}}` | Identifiant technique du projet (utilisé dans le code, les logs, les noms de services Docker) | `my-saas` |
| `{{PROJECT_SLUG}}` | Version minuscule sans tirets (URLs, noms de base de données, préfixes CSS) | `mysaas` |
| `{{PROJECT_DOMAIN}}` | Nom de domaine de production sans protocole (utilisé dans CORS, Traefik, emails) | `my-saas.com` |
| `{{PROJECT_DISPLAY_NAME}}` | Nom affiché dans l'interface (navbar, emails, onglets du navigateur) | `My SaaS Platform` |
| `{{DEFAULT_EMAIL}}` | Email de contact par défaut (footer, emails d'administration, support) | `contact@my-saas.com` |
| `{{PROJECT_TAGLINE}}` | Accroche affichée sur la page d'accueil (hero section, balises meta) | `La plateforme qui change tout` |
| `{{PRIMARY_COLOR}}` | Couleur principale de la charte graphique (code hexadécimal) | `#6366f1` |

### Comment remplacer les placeholders

**Option 1 — Script automatique (recommandé)**

Le script `replace_placeholders.py` parcourt tous les fichiers du template et remplace les valeurs de référence par des marqueurs `{{PLACEHOLDER}}`. Utilisez-le dans le sens inverse via `rename_project.py` :

```bash
# Initialiser un nouveau projet avec vos valeurs
python scripts/rename_project.py \
  --name "My SaaS Platform" \
  --slug "mysaas" \
  --domain "my-saas.com" \
  --display-name "My SaaS Platform" \
  --email "contact@my-saas.com" \
  --tagline "La plateforme qui change tout" \
  --color "#6366f1"
```

**Option 2 — Remplacement manuel (pour Claude Code ou Codex)**

Si vous utilisez un agent IA pour adapter le template, donnez-lui ce bloc de correspondances :

```
{{PROJECT_NAME}}         → my-saas
{{PROJECT_SLUG}}         → mysaas
{{PROJECT_DOMAIN}}       → my-saas.com
{{PROJECT_DISPLAY_NAME}} → My SaaS Platform
{{DEFAULT_EMAIL}}        → contact@my-saas.com
{{PROJECT_TAGLINE}}      → La plateforme qui change tout
{{PRIMARY_COLOR}}        → #6366f1
```

L'agent peut ensuite faire un rechercher/remplacer global sur l'ensemble du projet.

**Option 3 — Dry run pour vérifier avant d'appliquer**

```bash
# Voir quels fichiers seraient modifiés sans rien changer
python scripts/replace_placeholders.py --dry-run --root .
```

### Où sont utilisés les placeholders

```
{{PROJECT_NAME}}
  ├── backend/app/main.py          (titre de l'API FastAPI)
  ├── docker-compose.yml           (noms de services et réseaux)
  └── frontend/src/agent-dashboard/ (titre du dashboard)

{{PROJECT_DOMAIN}}
  ├── backend/app/main.py          (liste CORS autorisée)
  ├── docker-compose.prod.yml      (règles Traefik / HTTPS)
  └── backend/app/config.py        (FRONTEND_URL par défaut)

{{PROJECT_DISPLAY_NAME}}
  ├── frontend/src/pages/Landing.tsx  (hero section)
  ├── frontend/index.html             (balise <title>)
  └── backend/app/email/templates/    (emails transactionnels)

{{PROJECT_TAGLINE}}
  └── frontend/src/pages/Landing.tsx  (sous-titre hero)

{{DEFAULT_EMAIL}}
  ├── backend/app/config.py           (ADMIN_EMAIL par défaut)
  └── frontend/src/pages/Landing.tsx  (lien contact)

{{PRIMARY_COLOR}}
  └── frontend/src/index.css          (variable CSS --color-primary)
```

## 🎯 Bonnes Pratiques

1. **Remplacer tous les placeholders** avant le premier déploiement — utiliser le dry run pour vérifier qu'aucun n'a été oublié
2. **Ne jamais hardcoder** les valeurs projet dans le code — utiliser les placeholders pour faciliter les futures mises à jour du template
3. **Suivre la structure modulaire** pour les nouveaux services
4. **Tester avec Docker** avant le déploiement
5. **Documenter** chaque nouveau service

## 🔄 Mise à Jour du Template

Pour maintenir le template à jour:
1. **Isoler les changements génériques** des spécificités projet
2. **Documenter les breaking changes**
3. **Tester** avec un projet exemple

## 📚 Documentation

- `docs/architecture.md` - Architecture détaillée
- `docs/agentic-services.md` - Guide des services
- `docs/deployment.md` - Guide de déploiement

---

**Template Version**: 1.0.0
**Basé sur**: Z-HITL
**Date**: 2026-03-24
**Dernière mise à jour**: 2026-03-24