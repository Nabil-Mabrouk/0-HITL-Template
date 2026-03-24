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

## 🎯 Bonnes Pratiques

1. **Utiliser les placeholders** : `{{PROJECT_NAME}}`, `{{PROJECT_SLUG}}`
2. **Suivre la structure modulaire** pour nouveaux services
3. **Tester avec Docker** avant le déploiement
4. **Documenter** chaque nouveau service

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