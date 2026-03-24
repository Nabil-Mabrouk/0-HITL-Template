---
title: "Authentification et Internationalisation"
---

## Gestion Globale de l'État : AuthContext

Pour le projet **0-HITL**, nous avons besoin de savoir à tout moment si un utilisateur est connecté, quel est son rôle (Admin, Premium, User) et de gérer ses jetons d'accès. Nous utilisons la **Context API** de React pour centraliser ces informations.

```tsx
// src/context/AuthContext.tsx
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(
    localStorage.getItem("access_token")
  );

  // Vérification de la session au chargement
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) fetchProfile(token);
  }, []);

  // ... login, logout
}
```

## Stratégie de Sécurité : JWT et Cookies

Nous utilisons une stratégie hybride pour sécuriser les sessions :
1.  **Access Token :** Un JWT de courte durée stocké en `localStorage` pour les appels API.
2.  **Refresh Token :** Un jeton stocké dans un cookie **HttpOnly** côté backend. Cela permet de renouveler la session automatiquement sans exposer le jeton aux scripts malveillants (attaques XSS).

## Protection des Routes (Guards)

Toutes les pages ne sont pas accessibles à tout le monde. Nous avons créé des composants "Guards" pour encapsuler la logique d'accès :

*   **PrivateRoute :** Redirige vers `/login` si l'utilisateur n'est pas connecté.
*   **AdminRoute :** Vérifie que l'utilisateur a le rôle `admin`.
*   **GuestRoute :** Empêche un utilisateur déjà connecté d'accéder aux pages de login/register.

Exemple d'utilisation dans `App.tsx` :
```tsx
<Route path="/admin" element={
  <AdminRoute><AdminDashboard /></AdminRoute>
} />
```

## Internationalisation (i18n)

0-HITL est une plateforme bilingue (FR/EN). Nous utilisons `react-i18next` pour gérer les traductions sans recharger la page.

### Points clés de notre configuration :
*   **Détection automatique :** La langue est détectée via le navigateur ou le `localStorage`.
*   **Namespaces :** Les traductions sont découpées par domaine (auth, learn, admin) pour plus de clarté.
*   **Changement dynamique :** L'utilisateur peut basculer de langue instantanément via le `LangSelector` dans la Navbar.

```tsx
const { t, i18n } = useTranslation("common");
// Utilisation : {t("nav.learn")}
```

---

*L'infrastructure de sécurité et la langue étant en place, nous pouvons maintenant construire les fonctionnalités métier de notre université virtuelle dans le chapitre suivant.*
