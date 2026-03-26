# Monétisation avec Stripe : Boutique et Abonnements

## Introduction

Une plateforme SaaS ne peut survivre sans modèle économique. Le template 0-HITL intègre deux stratégies de monétisation complémentaires, toutes deux activables indépendamment via des variables d'environnement. Cette approche **feature-flag** permet de démarrer sans paiement et d'activer la monétisation uniquement quand vous êtes prêt.

```env
MONETIZATION_SHOP=true           # Vente de produits numériques (achat unique)
MONETIZATION_SUBSCRIPTION=true   # Abonnements récurrents → rôle premium
```

Les deux modes utilisent **Stripe**, la référence mondiale du paiement en ligne, via son **Hosted Checkout** — vous ne gérez jamais de numéros de carte en direct sur votre serveur.

## Architecture Webhook-First

La clé de fiabilité de ce système est son architecture **webhook-first**. Plutôt que de se fier à la redirection de l'utilisateur après paiement (qui peut échouer si le navigateur se ferme), le fulfillment s'appuie sur les événements envoyés directement par Stripe à votre serveur.

```
Utilisateur                    Frontend              Backend            Stripe
    │                             │                     │                  │
    │ Cliquer "Acheter"           │                     │                  │
    │──────────────────────────►  │                     │                  │
    │                             │ POST /api/shop/checkout                │
    │                             │──────────────────►  │                  │
    │                             │                     │ Create Session   │
    │                             │                     │─────────────────►│
    │                             │ {checkout_url}      │                  │
    │                             │◄──────────────────  │                  │
    │ Redirection Stripe          │                     │                  │
    │◄────────────────────────────│                     │                  │
    │                             │                     │                  │
    │ [Paiement sur Stripe]       │                     │                  │
    │                             │                     │                  │
    │                             │         POST /api/shop/webhook         │
    │                             │                     │◄─────────────────│
    │                             │                     │ checkout.session │
    │                             │                     │  .completed      │
    │                             │                     │                  │
    │                             │         Email avec lien de téléchargement
    │◄──────────────────────────────────────────────────│                  │
    │                             │                     │                  │
    │ Redirection /shop/success   │                     │                  │
    │──────────────────────────►  │                     │                  │
```

## Boutique de Produits Numériques

### Modèle de données

```python
class Product(Base):
    name            = Column(String)          # Affiché au client
    slug            = Column(String, unique=True)
    price_cents     = Column(Integer)         # 2900 = 29,00 €
    stripe_price_id = Column(String)          # price_… (depuis Stripe Dashboard)
    file_path       = Column(String)          # Chemin fichier sur le serveur
    is_active       = Column(Boolean)

class Purchase(Base):
    user_id           = Column(Integer, nullable=True)   # Nullable = achat invité
    product_id        = Column(Integer)
    email             = Column(String)
    stripe_session_id = Column(String, unique=True)
    download_token    = Column(String, unique=True)      # Token URL aléatoire
    download_count    = Column(Integer, default=0)
    max_downloads     = Column(Integer, default=5)
    token_expires_at  = Column(DateTime)
    fulfilled_at      = Column(DateTime)                 # Défini par le webhook
```

### Configurer un produit

**Étape 1 — Créer le produit dans Stripe Dashboard**

1. Stripe Dashboard → Products → Add Product
2. Définir le nom, la description, le prix en mode "One time"
3. Copier le `Price ID` (format `price_xxx`)

**Étape 2 — Créer le produit en base de données**

```bash
POST /api/admin/shop/products
Authorization: Bearer <admin_token>

{
  "name":            "Guide Complet FastAPI",
  "slug":            "guide-fastapi",
  "description":     "200 pages de référence pratique",
  "price_cents":     2900,
  "currency":        "eur",
  "stripe_price_id": "price_1ABC...",
  "file_path":       "/data/products/guide-fastapi.pdf",
  "cover_image":     "https://cdn.exemple.com/guide-cover.jpg"
}
```

**Étape 3 — Placer le fichier sur le serveur**

Le `file_path` doit pointer vers un fichier accessible par le conteneur backend. En production, montez un volume Docker :

```yaml
# docker-compose.prod.yml
services:
  backend:
    volumes:
      - /opt/my-app/products:/data/products:ro   # read-only pour le backend
```

### Sécurité des téléchargements

Le mécanisme de téléchargement est intentionnellement restrictif :

```python
@router.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(
        Purchase.download_token == token
    ).first()

    # Vérifications en cascade
    if not purchase or not purchase.fulfilled_at:
        raise HTTPException(404)                    # Token inconnu ou non payé
    if now > purchase.token_expires_at:
        raise HTTPException(410, "Lien expiré")     # Durée dépassée
    if purchase.download_count >= purchase.max_downloads:
        raise HTTPException(410, "Limite atteinte") # Trop de téléchargements

    purchase.download_count += 1
    db.commit()
    return FileResponse(purchase.product.file_path) # Servi par FastAPI
```

Les tokens sont des chaînes aléatoires de 48 octets (`secrets.token_urlsafe(48)`), impossibles à deviner. La durée de validité et le nombre maximum de téléchargements sont configurables dans `.env`.

## Abonnements Stripe

### Modèle de données

```python
class Subscription(Base):
    user_id                = Column(Integer, unique=True)   # 1 abonnement par user
    stripe_subscription_id = Column(String, unique=True)   # sub_…
    stripe_customer_id     = Column(String)                # cus_…
    stripe_price_id        = Column(String)                # plan souscrit
    status                 = Column(Enum(SubscriptionStatus))
    current_period_end     = Column(DateTime)
    trial_end              = Column(DateTime)
    cancelled_at           = Column(DateTime)
```

### Statuts et transitions

```
      [Création]
          │
          ▼
      trialing ────────────────────────────────────────────────►
          │                                                      │
          │ (fin d'essai + paiement ok)                         │
          ▼                                                      │
        active ──────────────────────────────────────────────►  │
          │                                                      │
          │ (échec paiement)     (annulation)                    │
          ▼                          ▼                           │
      past_due               cancelled ◄──────────────────────  │
          │                                                      │
          │ (toujours pas payé)                                  │
          ▼                                                      │
        unpaid                                                   │
                                                                 │
──► rôle premium accordé          rôle premium révoqué ◄────────┘
```

**La règle est simple :** `status in (active, trialing)` → rôle `premium`. Tout autre statut → rôle `user`. Cette logique est appliquée automatiquement dans les handlers webhook.

### Configurer un plan d'abonnement

**Dans Stripe Dashboard :**
1. Products → Add Product (choisir "Recurring")
2. Définir l'intervalle : mensuel, annuel, etc.
3. Copier le `Price ID` du plan

**L'API liste les plans disponibles automatiquement depuis Stripe :**
```bash
GET /api/subscription/plans
# Retourne tous les prices actifs de type recurring
```

### Essai gratuit

```env
MONETIZATION_TRIAL_DAYS=14   # 14 jours d'essai, puis facturation
```

Avec cette configuration, la session Stripe Checkout affiche automatiquement la période d'essai. Le rôle `premium` est accordé dès le début de l'essai (statut `trialing`).

### Customer Portal Stripe

Plutôt que de recoder une interface de gestion d'abonnement (changer de plan, mettre à jour la carte, annuler), nous déléguons entièrement à Stripe :

```bash
POST /api/subscription/portal
Authorization: Bearer <token>
{ "return_url": "https://votre-site.com/profile" }

# Réponse
{ "portal_url": "https://billing.stripe.com/session/..." }
```

L'utilisateur est redirigé vers un portail Stripe hébergé, puis renvoyé vers votre site via `return_url`.

## Webhook — Le Cœur du Système

L'endpoint `/api/shop/webhook` est le seul point d'entrée pour tous les événements Stripe. La signature est vérifiée à chaque appel.

```python
@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig     = request.headers.get("stripe-signature")

    # Vérification HMAC — rejette tout appel non signé par Stripe
    event = stripe.Webhook.construct_event(
        payload, sig, settings.stripe_webhook_secret
    )

    match event["type"]:
        case "checkout.session.completed":
            if event["data"]["object"]["mode"] == "payment":
                _fulfill_shop_purchase(db, ...)    # boutique
            else:
                _fulfill_subscription(db, ...)     # abonnement

        case "customer.subscription.updated":
            _update_subscription(db, ...)          # sync statut + rôle

        case "customer.subscription.deleted":
            _cancel_subscription(db, ...)          # révoque premium

        case "invoice.payment_succeeded":
            # Renouvellement ok → s'assurer que le statut est active
            ...
        case "invoice.payment_failed":
            # Mettre en past_due, notifier l'utilisateur
            ...
```

### Configurer le webhook en production

1. Stripe Dashboard → Developers → Webhooks → Add Endpoint
2. URL : `https://api.votre-domaine.com/api/shop/webhook`
3. Événements à sélectionner :
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copier le **Signing Secret** (`whsec_…`) → `STRIPE_WEBHOOK_SECRET` dans `.env`

### Tester en local

Stripe CLI permet de rediriger les webhooks vers votre serveur local :

```bash
# Installer Stripe CLI
brew install stripe/stripe-cli/stripe

# Écouter et rediriger vers le backend local
stripe listen --forward-to localhost:8000/api/shop/webhook

# Dans un autre terminal — simuler un paiement
stripe trigger checkout.session.completed
```

## Pages Frontend

### `/shop` — Catalogue produits

```tsx
// Chargement des produits publics (pas d'auth requise)
useEffect(() => {
    fetch(`${API}/api/shop/products`)
        .then(r => r.json())
        .then(setProducts);
}, []);

// Checkout — redirige vers Stripe
async function handleBuy(product: Product) {
    const res = await fetch(`${API}/api/shop/checkout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ product_slug: product.slug }),
    });
    const { checkout_url } = await res.json();
    window.location.href = checkout_url;   // Redirection vers Stripe
}
```

### `/premium` — Plans d'abonnement

La page charge les plans depuis Stripe en temps réel, affiche le statut de l'abonnement courant, et propose l'accès au Customer Portal Stripe pour gérer/annuler.

### Profil — Section "Mes achats"

La section **Mes achats** dans `/profile` liste tous les achats fulfilled de l'utilisateur avec :
- Nom du produit + date + montant payé
- Lien de téléchargement actif (si token valide et téléchargements restants)
- Indication "Lien expiré" sinon

## Checklist de Mise en Production

```
□ Créer un compte Stripe et activer le mode Production
□ Créer les produits/plans dans Stripe Dashboard
□ Renseigner STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY (clés live_)
□ Configurer le webhook Stripe et copier STRIPE_WEBHOOK_SECRET
□ Activer MONETIZATION_SHOP=true et/ou MONETIZATION_SUBSCRIPTION=true
□ Créer les produits en base via POST /api/admin/shop/products
□ Placer les fichiers dans le volume /data/products
□ Lancer la migration : alembic upgrade head
□ Tester un paiement avec une carte test Stripe (4242 4242 4242 4242)
□ Vérifier la réception de l'email de confirmation
□ Vérifier le lien de téléchargement
```

---

*La monétisation étant en place, votre plateforme 0-HITL est désormais complète : un produit, une audience, et des revenus. Dans la conclusion, nous récapitulerons l'ensemble de l'architecture construite et les prochaines étapes d'évolution.*
