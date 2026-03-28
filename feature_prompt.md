# Feature Development Prompt — 0-HITL Template

Ce fichier est un **prompt générique** pour demander à un agent LLM d'implémenter
une nouvelle fonctionnalité dans le template 0-HITL, sans casser le code existant.

---

## Comment utiliser ce prompt

```bash
claude "$(cat feature_prompt.md)"   # Claude Code CLI
gemini -p "$(cat feature_prompt.md)"    # Gemini CLI
```

**Avant de lancer**, remplissez uniquement la section `[DESCRIPTION DE LA FONCTIONNALITÉ]`
et choisissez un modèle d'accès dans `[MODÈLE D'ACCÈS]`.

---

---
## PROMPT À ENVOYER À L'AGENT LLM

---

### Rôle

Tu es un développeur fullstack expert en FastAPI et React. Ta mission est d'implémenter
une nouvelle fonctionnalité dans une application existante **sans modifier** le code
des fonctionnalités déjà en place — uniquement des ajouts et des branchements propres.

---

### Description de la fonctionnalité

[REMPLACER CE BLOC PAR VOTRE DESCRIPTION]

Soyez précis sur :
- Ce que fait la fonctionnalité (métier, flux utilisateur)
- Les données manipulées (quelles entités, quels champs)
- Les actions disponibles (lecture seule ? écriture ? upload ? calcul ?)
- L'interface souhaitée (page dédiée ? widget dans une page existante ? modal ?)
- Les limites pour les utilisateurs gratuits (si modèle freemium)

Exemple :
> Outil de génération de résumé IA : l'utilisateur colle un texte brut,
> clique sur "Résumer", et obtient un résumé structuré en bullet points.
> Les utilisateurs gratuits sont limités à 3 utilisations par jour.
> Les utilisateurs premium ont un accès illimité et peuvent choisir la longueur.
> Interface : page dédiée /summarize avec un textarea + bouton + zone de résultat.

---

### Modèle d'accès

Choisir un modèle parmi les trois ci-dessous (supprimer les deux autres) :

**Option A — Premium uniquement**
> La fonctionnalité est entièrement réservée aux utilisateurs premium et admin.
> Les utilisateurs `user` voient une page de upgrade, pas la fonctionnalité.

**Option B — Freemium (accès limité pour tous, complet pour premium)**
> Tous les utilisateurs authentifiés peuvent accéder à la fonctionnalité,
> mais avec des limites pour le rôle `user` :
> [PRÉCISER ICI LA LIMITE : ex. "3 appels/jour", "5 résultats max", "sans export PDF"]
> Les utilisateurs premium et admin ont un accès complet et sans limite.

**Option C — Tous les utilisateurs authentifiés**
> La fonctionnalité est accessible à tous les utilisateurs connectés et vérifiés
> (rôles `user`, `premium`, `admin`), sans distinction de niveau.

---

### Architecture du projet (à lire impérativement avant de coder)

#### Système de rôles

```
anonymous → waitlist → user → premium → admin
```

- `anonymous` : visiteur non connecté
- `waitlist`  : inscrit en liste d'attente, pas encore confirmé
- `user`      : utilisateur standard vérifié
- `premium`   : abonné avec accès aux fonctionnalités avancées
- `admin`     : accès complet

#### Dépendances d'authentification backend (ne PAS recréer, importer depuis le module existant)

```python
from app.auth.dependencies import (
    get_current_user,    # Utilisateur authentifié (401 sinon)
    get_optional_user,   # Utilisateur si connecté, None sinon — ne lève jamais d'erreur
    get_verified_user,   # Authentifié + email vérifié (403 sinon)
    require_user,        # Rôles : user + premium + admin
    require_premium,     # Rôles : premium + admin
    require_admin,       # Rôle  : admin uniquement
    require_role,        # Fabrique : require_role(UserRole.user, UserRole.premium)
)
from app.models import User, UserRole
```

#### Pattern freemium dans un endpoint

```python
@router.post("/my-feature")
async def my_feature(
    payload: MyRequest,
    current_user: User = Depends(require_user),  # user + premium + admin
    db: Session = Depends(get_db),
):
    is_premium = current_user.role in (UserRole.premium, UserRole.admin)

    if not is_premium:
        # Vérifier quota / appliquer limite
        usage_today = db.query(MyUsageModel).filter(
            MyUsageModel.user_id == current_user.id,
            MyUsageModel.created_at >= today_start,
        ).count()
        if usage_today >= FREE_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Limite quotidienne atteinte. Passez à Premium pour un accès illimité."
            )

    # Logique principale
    result = do_the_work(payload, full_access=is_premium)
    return result
```

#### Pattern premium uniquement dans un endpoint

```python
@router.get("/my-premium-feature")
async def my_premium_feature(
    current_user: User = Depends(require_premium),  # 403 automatique si pas premium
    db: Session = Depends(get_db),
):
    # Ici, current_user est garanti premium ou admin
    ...
```

#### Enregistrement du router dans `backend/app/main.py`

```python
# Ajouter l'import en haut avec les autres
from .routers import my_feature_router

# Ajouter dans la section app.include_router(...)
app.include_router(my_feature_router.router, prefix="/api")
```

#### AuthContext frontend — variables disponibles

```tsx
const { user, accessToken, isAdmin, isPremium, isLoading } = useAuth()

// Vérification du niveau d'accès
const isPremiumOrAdmin = user?.role === 'premium' || user?.role === 'admin'
```

#### Pattern freemium dans un composant React

```tsx
export default function MyFeaturePage() {
  const { user, isPremium } = useAuth()

  return (
    <PageTransition>
      <main className="min-h-screen ...">
        {/* Contenu accessible à tous */}
        <MyFeatureForm />

        {/* Résultat : affiché pour tous, avec limite pour les gratuits */}
        <MyFeatureResult />

        {/* Bannière upgrade — visible uniquement pour les non-premium */}
        {!isPremium && (
          <UpgradeBanner
            message="Vous avez atteint votre limite quotidienne."
            ctaLabel="Passer à Premium"
            ctaHref="/premium"
          />
        )}
      </main>
    </PageTransition>
  )
}
```

#### Pattern premium uniquement dans un composant React

```tsx
export default function MyPremiumFeaturePage() {
  const { user, isPremium, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && !isPremium) {
      navigate('/premium')   // Redirection vers la page d'upgrade
    }
  }, [isPremium, isLoading])

  if (isLoading || !isPremium) return null

  return (
    <PageTransition>
      <main>...</main>
    </PageTransition>
  )
}
```

---

### Ce que tu dois produire

#### Fichiers backend à CRÉER

| Fichier | Contenu |
|---|---|
| `backend/app/schemas/<feature>.py` | Schémas Pydantic (Request + Response) |
| `backend/app/routers/<feature>.py` | Router FastAPI avec tous les endpoints |
| `backend/alembic/versions/<hash>_feat_<feature>.py` | Migration Alembic **si et seulement si** de nouveaux modèles sont nécessaires |

#### Fichiers backend à MODIFIER (ajouts uniquement, pas de réécriture)

| Fichier | Modification |
|---|---|
| `backend/app/models.py` | Ajouter les nouveaux modèles SQLAlchemy **à la fin du fichier**, sans toucher aux modèles existants |
| `backend/app/main.py` | Ajouter l'import du router et `app.include_router(...)` dans la section dédiée |

#### Fichiers frontend à CRÉER

| Fichier | Contenu |
|---|---|
| `frontend/src/pages/<Feature>.tsx` | Page principale de la fonctionnalité |

#### Fichiers frontend à MODIFIER (ajouts uniquement)

| Fichier | Modification |
|---|---|
| `frontend/src/App.tsx` | Ajouter la `<Route>` dans la section appropriée (Public / PrivateRoute / etc.) |
| `frontend/src/components/Navbar.tsx` | Ajouter un lien de navigation **si la fonctionnalité mérite une entrée dans le menu** |
| `frontend/public/locales/fr/common.json` | Ajouter les clés i18n pour la nouvelle page |
| `frontend/public/locales/en/common.json` | Idem en anglais |

#### Fichiers à NE PAS toucher

- Tout ce qui existe dans `backend/app/routers/` sauf `main.py`
- `backend/app/auth/` (security, dependencies)
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/auth/AuthRouter.tsx`
- `frontend/src/pages/Login.tsx`, `Register.tsx`, `Profile.tsx`, `admin/`
- `frontend/src/theme.config.ts` (sauf si la feature nécessite un nouveau token de couleur)
- `frontend/vite.config.ts`, `backend/alembic/env.py`

---

### Règles de qualité à respecter

**Backend**
- Chaque endpoint doit avoir une docstring expliquant son rôle, ses paramètres et ses erreurs possibles
- Les erreurs métier retournent toujours un `HTTPException` avec un `detail` lisible par l'utilisateur
- Ne jamais retourner le mot de passe ou `hashed_password` dans une réponse
- Utiliser `response_model=` sur chaque endpoint pour contrôler la sérialisation
- Si la fonctionnalité a un quota, le vérifier en base avant d'exécuter l'opération coûteuse

**Frontend**
- Envelopper la page dans `<PageTransition>` pour la transition de route
- Utiliser `<FadeIn>`, `<StaggerGroup>/<StaggerItem>` pour animer les sections au scroll
- Les classes CSS utilisent les variables du thème : `text-primary`, `bg-background`, `border-border`
- Les textes passent par `useTranslation` + clés i18n
- Les appels API utilisent le pattern :
  ```tsx
  const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  const res = await fetch(`${API}/api/<endpoint>`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })
  ```
- Gérer les états : `isLoading`, `error`, résultat vide

**Migration Alembic** (si nouveau modèle)
- Nommer le fichier : `<timestamp_hex>_feat_<feature_slug>.py`
- La migration doit être réversible (`downgrade` doit supprimer ce que `upgrade` crée)
- Ne modifier aucune table existante dans la migration — uniquement des `CREATE TABLE` / `DROP TABLE`

---

### Livrable attendu

Pour chaque fichier, fournir le **code complet** (pas de `# ... existing code ...`
ni de diff partiel).

Accompagner le code d'une section **"Instructions de déploiement"** :
```
1. Appliquer la migration : docker-compose -f docker-compose.dev.yml run --rm migrate
2. Redémarrer le backend : docker-compose -f docker-compose.dev.yml restart backend
3. La page est accessible sur : http://localhost:5173/<route>
```

---
*Fin du prompt*
