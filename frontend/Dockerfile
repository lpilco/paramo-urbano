# ==============================================================================
# PÁRAMO URBANO (v2.0.0 Core) — Frontend Dockerfile (Multi-Stage Production Build)
# "Donde el asfalto toca la cumbre"
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Bundle Compilation
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using clean install
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source code and configurations
COPY frontend/ ./

# Verify TypeScript compilation and build production assets
RUN npm run typecheck && npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Nginx Static & SPA Serving
# ------------------------------------------------------------------------------
FROM nginx:alpine-slim AS runner

# Remove default Nginx website
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy pre-configured production Nginx configuration
COPY infra/docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Copy compiled SPA production assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Grant appropriate permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
