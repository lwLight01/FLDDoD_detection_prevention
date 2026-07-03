# ==============================================================================
# Admin Dashboard Dockerfile
# Build: React/TypeScript app (Vite) → Nginx static server
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 32
# ==============================================================================

# ── Stage 1: Node.js build ────────────────────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package manifests first (layer caching)
COPY src/dashboard/package*.json ./

# Install Node dependencies
RUN npm ci --silent

# Copy the rest of the dashboard source
COPY src/dashboard/ ./

# Build production bundle
RUN npm run build

# ── Stage 2: Nginx static server ──────────────────────────────────────────────
FROM nginx:alpine AS production

# Copy Nginx config for SPA routing (React Router)
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
