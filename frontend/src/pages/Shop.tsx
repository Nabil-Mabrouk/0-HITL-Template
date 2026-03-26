import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import SEO from "../components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Product {
  id:          number;
  name:        string;
  slug:        string;
  description: string | null;
  price_cents: number;
  currency:    string;
  cover_image: string | null;
}

function formatPrice(cents: number, currency: string) {
  return new Intl.NumberFormat("fr-FR", {
    style:    "currency",
    currency: currency.toUpperCase(),
  }).format(cents / 100);
}

export default function Shop() {
  const { accessToken } = useAuth();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [buying,   setBuying]   = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API}/api/shop/products`)
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(setProducts)
      .catch(() => setError("Impossible de charger la boutique."))
      .finally(() => setLoading(false));
  }, []);

  async function handleBuy(product: Product) {
    setBuying(product.id);
    try {
      const res = await fetch(`${API}/api/shop/checkout`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          product_slug: product.slug,
          success_url:  `${window.location.origin}/shop/success`,
          cancel_url:   `${window.location.origin}/shop`,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur paiement");
      }
      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erreur lors du paiement");
      setBuying(null);
    }
  }

  return (
    <>
      <SEO
        title="Boutique"
        description="Achetez nos produits numériques — téléchargement immédiat après paiement."
        url="/shop"
      />
      <main className="min-h-screen bg-black text-white px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Boutique</h1>
          <p className="text-white/60 mb-10">
            Produits numériques — téléchargement immédiat après paiement.
          </p>

          {loading && (
            <p className="text-white/40">Chargement…</p>
          )}

          {error && (
            <p className="text-red-400">{error}</p>
          )}

          {!loading && !error && products.length === 0 && (
            <p className="text-white/40">Aucun produit disponible pour l'instant.</p>
          )}

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {products.map(product => (
              <div
                key={product.id}
                className="border border-white/10 rounded-xl p-6 flex flex-col
                           hover:border-white/30 transition-colors"
              >
                {product.cover_image && (
                  <img
                    src={product.cover_image}
                    alt={product.name}
                    className="w-full h-40 object-cover rounded-lg mb-4"
                  />
                )}
                <h2 className="text-lg font-semibold mb-2">{product.name}</h2>
                {product.description && (
                  <p className="text-white/60 text-sm flex-1 mb-4">
                    {product.description}
                  </p>
                )}
                <div className="flex items-center justify-between mt-auto">
                  <span className="text-xl font-bold">
                    {formatPrice(product.price_cents, product.currency)}
                  </span>
                  <button
                    onClick={() => handleBuy(product)}
                    disabled={buying === product.id}
                    className="px-4 py-2 bg-white text-black rounded-lg
                               text-sm font-medium hover:bg-white/90
                               disabled:opacity-50 disabled:cursor-wait transition"
                  >
                    {buying === product.id ? "Redirection…" : "Acheter"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
