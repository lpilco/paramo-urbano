#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Script de Estado y Monitoreo
# "Donde el asfalto toca la cumbre"
#
# Monitorea el estado en vivo de:
# 1. Base de datos e Infraestructura Docker
# 2. Backend REST API (Uvicorn / FastAPI)
# 3. Telemetry Ingestion Worker
# 4. Frontend SPA Server
# 5. Túnel Público HTTPS
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colores de consola
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}📊  PÁRAMO URBANO — ESTADO DE SERVICIOS Y TÚNEL${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"

# 1. Docker
echo -e "\n${BOLD}[1] INFRAESTRUCTURA PERSISTENTE (DOCKER):${NC}"
if command -v docker &> /dev/null; then
    DOCKER_OUT=""
    (docker ps --filter "name=paramo" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" > "$PROJECT_ROOT/.run/docker_status.tmp" 2>/dev/null) &
    D_PID=$!
    D_WAIT=0
    while kill -0 "$D_PID" 2>/dev/null; do
        sleep 0.2
        D_WAIT=$((D_WAIT + 1))
        if [ "$D_WAIT" -ge 10 ]; then
            kill -9 "$D_PID" 2>/dev/null || true
            break
        fi
    done
    wait "$D_PID" 2>/dev/null || true

    if [ -f "$PROJECT_ROOT/.run/docker_status.tmp" ] && [ -s "$PROJECT_ROOT/.run/docker_status.tmp" ]; then
        cat "$PROJECT_ROOT/.run/docker_status.tmp"
        rm -f "$PROJECT_ROOT/.run/docker_status.tmp"
    else
        echo -e "  ${YELLOW}⚠️  Docker daemon no disponible o sin contenedores activos.${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Docker no está instalado en el sistema.${NC}"
fi

# 2. Backend API
echo -e "\n${BOLD}[2] BACKEND REST API (FASTAPI):${NC}"
BACKEND_PID_FILE="$PROJECT_ROOT/.run/backend.pid"
if [ -f "$BACKEND_PID_FILE" ] && ps -p "$(cat "$BACKEND_PID_FILE" 2>/dev/null)" > /dev/null 2>&1; then
    BPID=$(cat "$BACKEND_PID_FILE")
    HEALTH=$(curl -s "http://127.0.0.1:${BACKEND_PORT}/health" 2>/dev/null || echo "UNREACHABLE")
    echo -e "  Status:  ${GREEN}🟢 EN EJECUCIÓN${NC} (PID: ${BPID})"
    echo -e "  Puerto:  http://localhost:${BACKEND_PORT}"
    echo -e "  Swagger: http://localhost:${BACKEND_PORT}/docs"
    echo -e "  Health:  ${HEALTH}"
else
    if lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        LPID=$(lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t | head -n 1)
        echo -e "  Status:  ${GREEN}🟢 ACTIVO EN PUERTO ${BACKEND_PORT}${NC} (PID detectado: ${LPID})"
    else
        echo -e "  Status:  ${RED}🔴 DETENIDO${NC}"
    fi
fi

# 3. Telemetry Worker
echo -e "\n${BOLD}[3] TELEMETRY INGESTION WORKER:${NC}"
WORKER_PID_FILE="$PROJECT_ROOT/.run/worker.pid"
if [ -f "$WORKER_PID_FILE" ] && ps -p "$(cat "$WORKER_PID_FILE" 2>/dev/null)" > /dev/null 2>&1; then
    WPID=$(cat "$WORKER_PID_FILE")
    echo -e "  Status:  ${GREEN}🟢 EN EJECUCIÓN${NC} (PID: ${WPID})"
    echo -e "  Logs:    logs/worker.log"
else
    echo -e "  Status:  ${RED}🔴 DETENIDO${NC}"
fi

# 4. Frontend SPA
echo -e "\n${BOLD}[4] FRONTEND WEB SPA:${NC}"
FRONTEND_PID_FILE="$PROJECT_ROOT/.run/frontend.pid"
if [ -f "$FRONTEND_PID_FILE" ] && ps -p "$(cat "$FRONTEND_PID_FILE" 2>/dev/null)" > /dev/null 2>&1; then
    FPID=$(cat "$FRONTEND_PID_FILE")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${FRONTEND_PORT}/" 2>/dev/null || echo "000")
    echo -e "  Status:  ${GREEN}🟢 EN EJECUCIÓN${NC} (PID: ${FPID})"
    echo -e "  URL:     http://localhost:${FRONTEND_PORT}"
    echo -e "  HTTP:    Respuesta ${HTTP_CODE}"
else
    if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        LPID=$(lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t | head -n 1)
        echo -e "  Status:  ${GREEN}🟢 ACTIVO EN PUERTO ${FRONTEND_PORT}${NC} (PID detectado: ${LPID})"
    else
        echo -e "  Status:  ${RED}🔴 DETENIDO${NC}"
    fi
fi

# 5. Túnel Público HTTPS
echo -e "\n${BOLD}[5] TÚNEL PÚBLICO HTTPS EN LÍNEA:${NC}"
TUNNEL_PID_FILE="$PROJECT_ROOT/.run/tunnel.pid"
TUNNEL_URL_FILE="$PROJECT_ROOT/.run/tunnel_url.txt"
TUNNEL_ACTIVE=false

if [ -f "$TUNNEL_PID_FILE" ] && ps -p "$(cat "$TUNNEL_PID_FILE" 2>/dev/null)" > /dev/null 2>&1; then
    TUNNEL_ACTIVE=true
    TPID=$(cat "$TUNNEL_PID_FILE")
elif pgrep -f "cloudflared tunnel --url" > /dev/null 2>&1; then
    TUNNEL_ACTIVE=true
    TPID=$(pgrep -f "cloudflared tunnel --url" | head -n 1)
fi

if [ "$TUNNEL_ACTIVE" = true ]; then
    PUBLIC_URL=""
    if [ -f "$TUNNEL_URL_FILE" ]; then
        PUBLIC_URL=$(cat "$TUNNEL_URL_FILE")
    fi
    if [ -z "$PUBLIC_URL" ]; then
        PUBLIC_URL=$(grep -E -o "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" "$PROJECT_ROOT/logs/tunnel.log" 2>/dev/null | tail -n 1 || true)
    fi

    echo -e "  Status:  ${GREEN}🟢 ACTIVO EN LÍNEA${NC} (PID: ${TPID})"
    if [ -n "$PUBLIC_URL" ]; then
        echo -e "  URL:     ${CYAN}${BOLD}${PUBLIC_URL}${NC}"
    else
        echo -e "  URL:     ${YELLOW}Obteniendo enlace... (consulta logs/tunnel.log)${NC}"
    fi
else
    echo -e "  Status:  ${RED}🔴 DETENIDO / SIN TÚNEL${NC}"
fi

echo -e "\n${CYAN}${BOLD}------------------------------------------------------------${NC}"
echo -e "  📜 Monitorear logs en vivo:"
echo -e "    Backend:   tail -f logs/backend.log"
echo -e "    Frontend:  tail -f logs/frontend.log"
echo -e "    Worker:    tail -f logs/worker.log"
echo -e "    Túnel:     tail -f logs/tunnel.log"
echo -e "${CYAN}${BOLD}============================================================${NC}"
