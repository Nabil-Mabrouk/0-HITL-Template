# Dockerisation Avancée pour la Production

## Introduction

Le passage du développement à la production nécessite une approche différente de Docker. Si en local nous privilégions le confort (rechargement à chaud, ports exposés), en production nous devons viser la performance, la sécurité et la légèreté. Dans ce chapitre, nous allons décortiquer les Dockerfiles optimisés du projet **0-HITL**.

## Le Pattern Multi-Stage

Le "Multi-Stage build" est la technique de référence pour créer des images de production. Elle consiste à utiliser une image pour compiler ou construire l'application, puis à copier uniquement le résultat final dans une image de base très légère.

### Backend (FastAPI)
L'image finale de 0-HITL ne contient pas les outils de compilation Python, seulement les dépendances installées et le code source.
*   **Stage 1 (Builder) :** Installe les dépendances via `pip install --user`.
*   **Stage 2 (Production) :** Récupère uniquement le dossier `.local` et le code de l'application.

### Frontend (React/Vite)
Pour React, le gain est encore plus impressionnant :
*   **Stage 1 & 2 :** Installation des modules npm et exécution de `npm run build`.
*   **Stage 3 (Production) :** Copie uniquement le dossier `dist` (quelques Mo de JS/CSS statique) et utilise un serveur léger comme `serve` pour les mettre à disposition.

## Sécurité des Conteneurs

Une règle d'or en production : **Ne jamais lancer de conteneur en tant qu'utilisateur root.**
Dans nos Dockerfiles, nous créons systématiquement un utilisateur système (`appuser`) aux droits restreints. Si un attaquant parvient à exploiter une faille dans l'application, il sera confiné dans le conteneur sans pouvoir impacter l'hôte.

```dockerfile
# Exemple dans le Dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

## Serveur de Production : Gunicorn + Uvicorn

En développement, nous utilisons `uvicorn --reload`. En production, nous utilisons **Gunicorn** comme gestionnaire de processus, qui orchestre plusieurs "workers" Uvicorn. Cela permet de traiter plusieurs requêtes simultanément et de redémarrer automatiquement un worker s'il échoue.

```bash
# Commande de lancement en production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Surveillance de l'État (Healthchecks)

Pour que notre orchestrateur (ou Traefik) sache si un conteneur est réellement prêt à recevoir du trafic, nous intégrons une instruction `HEALTHCHECK`. Elle interroge l'endpoint `/health` toutes le 30 secondes.

---

*Notre infrastructure est désormais robuste et prête pour le monde réel. Il est temps de conclure ce premier tome en faisant le bilan de notre parcours dans le dernier chapitre.*
