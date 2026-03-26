import { Link } from "react-router-dom";
import SEO from "../components/SEO";

export default function ShopSuccess() {
  return (
    <>
      <SEO title="Achat confirmé" noindex={true} />
      <main className="min-h-screen bg-black text-white flex flex-col
                       items-center justify-center px-4 text-center">
        <div className="text-5xl mb-6">🎉</div>
        <h1 className="text-3xl font-bold mb-3">Merci pour votre achat !</h1>
        <p className="text-white/60 mb-2 max-w-md">
          Votre paiement a bien été reçu. Vous allez recevoir un email avec
          votre lien de téléchargement dans quelques secondes.
        </p>
        <p className="text-white/40 text-sm mb-8">
          Si vous avez un compte, retrouvez vos achats dans votre profil.
        </p>
        <div className="flex gap-4">
          <Link
            to="/profile"
            className="px-5 py-2.5 bg-white text-black rounded-lg font-medium
                       hover:bg-white/90 transition"
          >
            Mon profil
          </Link>
          <Link
            to="/shop"
            className="px-5 py-2.5 border border-white/20 rounded-lg
                       hover:border-white/40 transition"
          >
            Retour à la boutique
          </Link>
        </div>
      </main>
    </>
  );
}
