# L'API Core et les Services Intelligents

## Introduction

Une API moderne ne se contente pas de déplacer des données entre une base de données et un client. Dans le projet **0-HITL**, le backend joue un rôle actif via des services spécialisés : un moteur d'évaluation dynamique pour l'onboarding et un système de tracking analytique respectueux de la vie privée.

## Validation des Données avec Pydantic

FastAPI utilise **Pydantic** pour valider les données entrantes et sortantes. Cela nous permet de définir des contrats clairs entre le frontend et le backend.

```python
# app/schemas/onboarding.py
from pydantic import BaseModel

class OnboardingAnswer(BaseModel):
    flow_id: str
    answers: dict[str, str]

class OnboardingResult(BaseModel):
    title: str
    description: str
    score: int
    profile: str
    label: str
```

Grâce à ces schémas, FastAPI génère automatiquement la documentation Swagger et rejette toute requête mal formée avant même qu'elle n'atteigne notre logique métier.

## Moteur d'Onboarding Dynamique

Le cœur du profilage des utilisateurs de 0-HITL repose sur un moteur qui évalue des "flows" au format JSON. Cette approche permet de modifier les règles métier (le scoring) sans toucher au code Python.

### Fonctionnement du Moteur :
1.  **Chargement :** Lecture du fichier JSON correspondant au `flow_id`.
2.  **Évaluation :** Comparaison des réponses de l'utilisateur avec les règles définies.
3.  **Résultat :** Attribution d'un profil (ex: *Builder*, *Architect*) et d'un score.

```python
def evaluate_scoring(flow: dict, answers: dict[str, str]) -> dict:
    rules = flow.get("scoring", {}).get("rules", [])
    for rule in rules:
        if all(answers.get(key) == val for key, val in rule["conditions"].items()):
            return rule["result"]
    return flow["scoring"]["default"]
```

## Tracking Analytique et GeoIP

Pour piloter la plateforme par la donnée tout en restant conforme au **RGPD**, nous avons implémenté un `TrackingMiddleware`.

### Un Tracking Non-Bloquant
Il est crucial que l'enregistrement d'une visite ne ralentisse pas la réponse de l'API. Nous utilisons `asyncio.get_running_loop().run_in_executor` pour déléguer l'écriture en base de données à un thread séparé.

### Géolocalisation Anonymisée
Nous utilisons le service **MaxMind GeoLite2** pour convertir l'IP du visiteur en données géographiques (pays, ville). L'IP réelle n'est jamais stockée ; seul un hash salé (`ip_hash`) est conservé pour identifier les visiteurs uniques sans les tracer individuellement.

```python
def _store_visit(ip: str, path: str, user_id: int | None):
    geo = geolocate(ip) # Service GeoIP local
    visit = Visit(
        ip_hash=hash_ip(ip),
        country_code=geo["country_code"],
        city=geo["city"],
        path=path,
        user_id=user_id
    )
    # Persistance asynchrone...
```

## API Agentic IA pour l'Automatisation

Au-delà des services de base, 0-HITL intègre un framework complet d'agents IA permettant d'automatiser des tâches complexes. Cette API expose des services pré-configurés (News Scraper, Research Assistant, Crypto Analyst) via un système d'orchestration multi-agents.

### Architecture du Framework Agentic

Le système repose sur cinq composants :
1. **Service Registry** : Gestion des services via configuration YAML
2. **Tool Registry** : Catalogue d'outils disponibles pour les agents
3. **Orchestrator** : Coordination des workflows multi-étapes
4. **Memory System** : Persistance du contexte entre les exécutions
5. **Guardrails** : Contrôles de sécurité et validation

### Endpoints Principaux

```python
# Liste des services disponibles
GET /api/agent-services/services

# Exécution d'un service
POST /api/agent-services/services/{service_slug}/execute
Body: {"workflow_name": "daily_news_digest", "parameters": {...}}

# Suivi des exécutions
GET /api/agent-services/executions/{execution_id}
```

### Exemple de Service : News Scraper

```yaml
# backend/app/config/agent_services.yaml
news_scraper:
  enabled: true
  name: "News Scraper"
  description: "Scrape l'actualité et génère des tweets automatiquement"
  agents:
    - name: "news_fetcher"
      model: "gpt-4"
      tools: ["web_scraper", "rss_reader", "news_api"]
    - name: "tweet_writer"
      model: "claude-3-sonnet"
      tools: ["tone_analyzer", "hashtag_generator"]
  workflows:
    - name: "daily_news_digest"
      steps: ["fetch_news", "summarize", "generate_tweets"]
```

### Modèles de Données Associés

Pour tracer les exécutions, le framework utilise des tables dédiées :
- `service_executions` : Exécutions complètes
- `service_execution_steps` : Étapes individuelles
- `service_results` : Résultats (textes, fichiers, médias)
- `user_service_preferences` : Préférences par utilisateur

---

*Avec une API robuste comprenant à la fois des services de base (onboarding, tracking) et un framework avancé d'agents IA, notre backend est prêt. Dans la partie suivante, nous allons construire l'interface utilisateur pour interagir avec ce "cerveau" technique, y compris le dashboard agentic.*
