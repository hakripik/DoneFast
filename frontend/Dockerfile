# Study Assistant frontend — Vite + React, built to static files and served
# by nginx, which also reverse-proxies /api/* to the backend container.

# ---- Stage 1: build the static bundle ----
FROM node:22-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked into the built JS bundle at build time — see src/lib/api.js. In Docker
# the frontend calls /api/* (proxied by nginx.conf below) instead of the
# localhost:8000 URL used for local `npm run dev`.
ENV VITE_API_BASE=/api
RUN npm run build

# ---- Stage 2: serve the build — no node_modules or dev tooling shipped ----
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173
