# Zero-Human In The Loop: a template for Agentic AI Platform

Un template complet pour projets web avec services agentic IA intégrés.

## 🚀 Fonctionnalités

### Backend (FastAPI)
- ✅ Authentification utilisateur (JWT, OAuth2)
- ✅ Gestion des utilisateurs et permissions
- ✅ Base de données PostgreSQL avec Alembic migrations
- ✅ API REST complète
- ✅ Services agentic IA modulaires
- ✅ Orchestrateur d'agents
- ✅ Mémoire et garde-fous
- ✅ Email, tracking, analytics
- ✅ Dashboard admin

### Frontend (React/TypeScript)
- ✅ Landing page responsive
- ✅ Dashboard utilisateur
- ✅ Interface pour services agentic IA
- ✅ Composants réutilisables
- ✅ Dark/light mode
- ✅ Gestion d'état (Redux/Context)

### Services Agentic IA
- ✅ Architecture modulaire
- ✅ Système de plugins
- ✅ Template pour nouveaux services
- ✅ API unifiée
- ✅ Historique des exécutions
- ✅ Dashboard unifié

## 📁 Structure du Projet

```
template-agentic-ai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # Services agentic IA
│   │   ├── auth/          # Authentification
│   │   ├── routers/       # Endpoints API
│   │   └── models.py     # Modèles SQLAlchemy
│   └── requirements.txt
├── frontend/              # React frontend
│   ├── src/
│   │   ├── agent-dashboard/  # Dashboard services IA
│   │   ├── agent-services/   # Composants services
│   │   └── agent-commons/    # Composants partagés
│   └── package.json
├── docker-compose.yml     # Déploiement Docker
└── scripts/              # Scripts utilitaires
```

## 🛠️ Installation Rapide

1. **Cloner le template**
```bash
git clone <template-url> my-project
cd my-project
```

2. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

3. **Lancer avec Docker**
```bash
docker-compose up -d
```

4. **Accéder à l'application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🎯 Personnalisation

### 1. Renommer le projet
```bash
python scripts/rename_project.py "MonNouveauProjet"
```

### 2. Ajouter un service agentic IA
```bash
# Créer un nouveau service
python scripts/create_service.py "nom_du_service" "Nom du Service"
```

### 3. Configurer les services existants
```yaml
# config/agent_services.yaml
services:
  news_scraper:
    enabled: true
    name: "Scraper d'Actualités"
    # ...
```

## 📚 Documentation

- [Architecture détaillée](docs/architecture.md)
- [Guide des services agentic IA](docs/agentic-services.md)
- [API Reference](docs/api-reference.md)
- [Déploiement](docs/deployment.md)

## 🔧 Services Exemples Inclus

1. **News Scraper** - Scrape l'actualité et génère des tweets
2. **Research Assistant** - Recherche bibliographique et rapports
3. **Crypto Analyst** - Analyse de marché et rapports multimédia
4. **Template Service** - Structure pour nouveaux services

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

---

**Template créé le**: 2026-03-24
**Version**: 1.0.0
**Dernière mise à jour**: 2026-03-24