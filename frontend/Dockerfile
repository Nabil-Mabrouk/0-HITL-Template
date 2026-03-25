FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production --legacy-peer-deps

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
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

FROM node:20-alpine AS production
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/package.json ./
RUN npm install -g serve@14
USER appuser
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]