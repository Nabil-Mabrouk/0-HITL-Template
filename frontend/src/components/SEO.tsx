import { Helmet } from "react-helmet-async";

interface SEOProps {
  title:        string;
  description?: string;
  image?:       string;
  url?:         string;
  type?:        "website" | "article";
  noindex?:     boolean;
  jsonLd?:      object;
}

const SITE_NAME    = import.meta.env.VITE_SITE_NAME ?? "0-HITL";
const SITE_URL     = import.meta.env.VITE_SITE_URL  ?? "https://0-hitl.com";
const DEFAULT_IMG  = `${SITE_URL}/og-default.png`;

export default function SEO({
  title,
  description = "L'automatisation intelligente arrive.",
  image       = DEFAULT_IMG,
  url,
  type        = "website",
  noindex     = false,
  jsonLd,
}: SEOProps) {
  const fullTitle    = `${title} | ${SITE_NAME}`;
  const canonicalUrl = url ? `${SITE_URL}${url}` : undefined;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description"        content={description} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}

      {/* Open Graph */}
      <meta property="og:title"       content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image"       content={image} />
      <meta property="og:type"        content={type} />
      <meta property="og:site_name"   content={SITE_NAME} />
      {canonicalUrl && <meta property="og:url" content={canonicalUrl} />}

      {/* Twitter Card */}
      <meta name="twitter:card"        content="summary_large_image" />
      <meta name="twitter:title"       content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image"       content={image} />

      {/* JSON-LD */}
      {jsonLd && (
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      )}
    </Helmet>
  );
}
