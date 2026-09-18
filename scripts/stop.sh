#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Script de Apagado Unificado
# "Donde el asfalto toca la cumbre"
#
# Detiene de forma ordenada:
# 1. Túnel público HTTPS (Cloudflare Tunnel o ngrok).
# 2. Servidor Web Frontend (Node.js en puerto 3000).
# 3. Telemetry Ingestion Worker (Background queue).
# 4. Backend REST API (FastAPI / Uvicorn en puerto 8000).
# 5. Opcional: Contenedores Docker (PostgreSQL, Redis, MinIO) si se pasa --with-docker o --all.
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

STOP_DOCKER=false
for arg in "$@"; do
    case $arg in
        --with-docker|--all|-d)
            STOP_DOCKER=true
            shift
            ;;
    esac
done

echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}🛑  PÁRAMO URBANO — APAGADO DE SERVICIOS Y TÚNEL${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"

# Función para detener un proceso por archivo PID con fallback seguro
stop_process() {
    local service_name="$1"
    local pid_file="$PROJECT_ROOT/.run/$2"

    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file" 2>/dev/null || true)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            echo -e "  🔻 Deteniendo ${service_name} (PID: ${pid})..."
            kill -15 "$pid" 2>/dev/null || true

            # Esperar hasta 4 segundos a que termine limpiamente
            local stopped=false
            for i in {1..8}; do
                if ! ps -p "$pid" > /dev/null 2>&1; then
                    stopped=true
                    break
                fi
                sleep 0.5
            done

            if [ "$stopped" = false ]; then
                echo -e "  ⚠️  ${service_name} no respondió a SIGTERM. Forzando detención (SIGKILL)..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo -e "  ${GREEN}✓ ${service_name} detenido.${NC}"
        else
            echo -e "  ℹ️  ${service_name} no estaba en ejecución activa."
        fi
        rm -f "$pid_file"
    else
        echo -e "  ℹ️  No hay PID registrado para ${service_name}."
    fi
}

# 1. Detener Túnel Público
echo -e "\n${BOLD}[1/4] Deteniendo Túnel Público...${NC}"
stop_process "Túnel Público" "tunnel.pid"
rm -f "$PROJECT_ROOT/.run/tunnel_url.txt"

# Limpieza adicional de procesos huérfanos de cloudflared vinculados al puerto 3000
if pgrep -f "cloudflared tunnel --url" > /dev/null 2>&1; then
    echo -e "  🧹 Limpiando procesos de cloudflared activos..."
    pkill -f "cloudflared tunnel --url" 2>/dev/null || true
fi

# 2. Detener Frontend SPA
echo -e "\n${BOLD}[2/4] Deteniendo Frontend SPA...${NC}"
stop_process "Frontend SPA" "frontend.pid"

# Verificación de puerto 3000
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  🧹 Liberando puerto ${FRONTEND_PORT}..."
    lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

# 3. Detener Worker de Telemetría
echo -e "\n${BOLD}[3/4] Deteniendo Ingestion Worker...${NC}"
stop_process "Telemetry Worker" "worker.pid"

# Limpieza adicional de procesos worker python huérfanos
if pgrep -f "backend.src.infrastructure.queue.worker" > /dev/null 2>&1; then
    pkill -f "backend.src.infrastructure.queue.worker" 2>/dev/null || true
fi

# 4. Detener Backend API
echo -e "\n${BOLD}[4/4] Deteniendo Backend REST API (Uvicorn)...${NC}"
stop_process "Backend REST API" "backend.pid"

# Verificación de puerto 8000
BACKEND_PORT="${BACKEND_PORT:-8000}"
if lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  🧹 Liberando puerto ${BACKEND_PORT}..."
    lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

# 5. Servicios Docker (Opcional)
if [ "$STOP_DOCKER" = true ]; then
    echo -e "\n${BOLD}[Docker] Deteniendo contenedores de infraestructura...${NC}"
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        docker compose -f "$PROJECT_ROOT/infra/docker/docker-compose.yml" stop
        echo -e "  ${GREEN}✓ Contenedores PostgreSQL, Redis y MinIO detenidos.${NC}"
    fi
else
    echo -e "\n  ℹ️  ${YELLOW}Contenedores Docker mantenidos en segundo plano para conservar persistencia y caché.${NC}"
    echo -e "     (Si deseas detener también Docker, ejecuta: ${BOLD}./scripts/stop.sh --all${NC})"
fi

echo -e "\n${CYAN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}✅ Todos los servidores y el túnel han sido apagados exitosamente.${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
