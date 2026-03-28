# ── Stage 1 : build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Installer les dépendances (devDeps incluses — requises par vite/tsc/tailwind)
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copier les sources et injecter les variables de build
COPY . .
ARG VITE_API_URL
ARG VITE_SITE_URL
ARG VITE_SITE_NAME
ARG VITE_AUTH_CHANNEL_WAITLIST
ARG VITE_AUTH_CHANNEL_DIRECT
ARG VITE_AUTH_CHANNEL_ONBOARDING
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SITE_URL=$VITE_SITE_URL
ENV VITE_SITE_NAME=$VITE_SITE_NAME
ENV VITE_AUTH_CHANNEL_WAITLIST=$VITE_AUTH_CHANNEL_WAITLIST
ENV VITE_AUTH_CHANNEL_DIRECT=$VITE_AUTH_CHANNEL_DIRECT
ENV VITE_AUTH_CHANNEL_ONBOARDING=$VITE_AUTH_CHANNEL_ONBOARDING
RUN npm run build

# ── Stage 2 : production ──────────────────────────────────────────────────────
FROM node:20-alpine AS production

# Utilisateur non-root pour la sécurité
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Installer `serve` globalement (avant le switch utilisateur)
RUN npm install -g serve

WORKDIR /app

# Copier uniquement le build statique — pas de node_modules en production
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist

USER appuser
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
