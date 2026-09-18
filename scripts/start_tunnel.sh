#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Secure Public Tunnel Exposure Script
# Exposes the frontend SPA (port 3000) with automatic reverse-proxy to FastAPI (port 8000)
# Supports Cloudflare Tunnel (cloudflared) or ngrok.
# ==============================================================================

set -eo pipefail

FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

echo "============================================================"
echo "🏔️  PÁRAMO URBANO — EXPOSICIÓN PÚBLICA SEGURA (HTTPS)"
echo "   Donde el asfalto toca la cumbre"
echo "============================================================"
echo "Puerto Frontend SPA: http://localhost:${FRONTEND_PORT}"
echo "Puerto Backend API:  http://localhost:${BACKEND_PORT}"
echo "Nota: El servidor frontend reverse-proxifica /api/* a FastAPI (${BACKEND_PORT}),"
echo "por lo que exponer el puerto ${FRONTEND_PORT} proporciona acceso completo a la SPA y API."
echo "------------------------------------------------------------"

if command -v cloudflared &> /dev/null; then
    echo "⚡ [Cloudflare Tunnel detectado]: Levantando túnel HTTPS seguro sin configuración previa..."
    echo "   Presiona CTRL+C para detener el túnel."
    echo ""
    cloudflared tunnel --url "http://localhost:${FRONTEND_PORT}"
elif command -v ngrok &> /dev/null; then
    echo "⚡ [ngrok detectado]: Levantando túnel HTTP en el puerto ${FRONTEND_PORT}..."
    echo "   Presiona CTRL+C para detener el túnel."
    echo ""
    ngrok http "${FRONTEND_PORT}"
else
    echo "❌ [ERROR] No se encontró ninguna herramienta de túnel instalada ('cloudflared' o 'ngrok')."
    echo ""
    echo "Opciones para instalar:"
    echo "1. Cloudflare Tunnel (Recomendado, gratuito, sin registro):"
    echo "   macOS (Homebrew): brew install cloudflared"
    echo "   Linux: sudo apt install cloudflared o descarga desde https://github.com/cloudflare/cloudflared/releases"
    echo ""
    echo "2. ngrok:"
    echo "   macOS (Homebrew): brew install ngrok/ngrok/ngrok"
    echo "   Web: https://ngrok.com/download"
    echo ""
    echo "Una vez instalado, vuelve a ejecutar este script:"
    echo "   bash scripts/start_tunnel.sh"
    exit 1
fi
