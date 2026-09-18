#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Script de Inicio Unificado
# "Donde el asfalto toca la cumbre"
#
# Inicia:
# 1. Servicios Docker (PostgreSQL, Redis, MinIO) si Docker está disponible.
# 2. Backend REST API con FastAPI / Uvicorn (puerto 8000).
# 3. Telemetry Ingestion Worker (cola asíncrona de procesamiento).
# 4. Frontend SPA (servidor Node en puerto 3000 con reverse-proxy a API).
# 5. Túnel público seguro HTTPS (Cloudflare Tunnel o ngrok).
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
NC='\033[0m' # Sin color

echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}🏔️  PÁRAMO URBANO (v2.0.0 Core) — ARRANQUE DEL SISTEMA${NC}"
echo -e "   Donde el asfalto toca la cumbre"
echo -e "${CYAN}${BOLD}============================================================${NC}"

# Opciones de ejecución
START_DOCKER=true
START_TUNNEL=true

for arg in "$@"; do
    case $arg in
        --no-docker|--skip-docker|--sqlite)
            START_DOCKER=false
            shift
            ;;
        --no-tunnel|--local-only)
            START_TUNNEL=false
            shift
            ;;
    esac
done

# 1. Preparar directorios de logs y PIDs
mkdir -p "$PROJECT_ROOT/logs" "$PROJECT_ROOT/.run"

# 2. Verificar archivo .env
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo -e "${YELLOW}⚠️  Archivo .env no encontrado. Creando a partir de .env.example...${NC}"
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    else
        echo -e "${RED}❌  Archivo .env y .env.example no encontrados.${NC}"
        exit 1
    fi
fi

# Cargar variables de entorno principales
set -a
# shellcheck disable=SC1091
source "$PROJECT_ROOT/.env"
set +a

FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# 3. Validar entorno Python (.venv)
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_UVICORN="$PROJECT_ROOT/.venv/bin/uvicorn"

if [ ! -x "$VENV_PYTHON" ] || [ ! -x "$VENV_UVICORN" ]; then
    echo -e "${RED}❌ Entorno virtual Python (.venv) no encontrado o incompleto.${NC}"
    echo "   Por favor ejecuta: python3 -m venv .venv && source .venv/bin/activate && pip install -e backend/"
    exit 1
fi

# 4. Validar Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js no está instalado o no se encuentra en el PATH.${NC}"
    exit 1
fi

# 5. Infraestructura Docker (PostgreSQL 16, Redis 7, MinIO)
echo -e "\n${BOLD}[1/5] Verificando Servicios de Infraestructura (Docker)...${NC}"
if [ "$START_DOCKER" = true ]; then
    if command -v docker &> /dev/null; then
        echo -e "  🐳 Intentando levantar contenedores con Docker Compose (timeout 5s)..."
        (docker compose -f "$PROJECT_ROOT/infra/docker/docker-compose.yml" up -d > "$PROJECT_ROOT/logs/docker_compose.log" 2>&1) &
        DOCKER_PID=$!
        D_WAITED=0
        D_SUCCESS=false

        while kill -0 "$DOCKER_PID" 2>/dev/null; do
            sleep 0.5
            D_WAITED=$((D_WAITED + 1))
            if [ "$D_WAITED" -ge 10 ]; then
                echo -e "  ${YELLOW}⚠️  Docker tardó más de 5s en responder (daemon ocupado o pausado).${NC}"
                kill -9 "$DOCKER_PID" 2>/dev/null || true
                break
            fi
        done

        if wait "$DOCKER_PID" 2>/dev/null; then
            D_SUCCESS=true
        fi

        if [ "$D_SUCCESS" = true ]; then
            echo -e "  ${GREEN}✓ Servicios de base de datos, colas y storage iniciados en Docker.${NC}"
        else
            echo -e "  ${YELLOW}ℹ️  El backend activará automáticamente el modo de respaldo SQLite (paramo_urbano_dev.db).${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  Docker no instalado. Modo de respaldo SQLite activo.${NC}"
    fi
else
    echo -e "  ${YELLOW}ℹ️  Flag --no-docker detectado. Saltando Docker (SQLite activo).${NC}"
fi

# 6. Backend API (FastAPI / Uvicorn)
echo -e "\n${BOLD}[2/5] Levantando Servidor Backend API (Puerto ${BACKEND_PORT})...${NC}"
BACKEND_PID_FILE="$PROJECT_ROOT/.run/backend.pid"

if lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null ; then
    EXISTING_BACKEND_PID=$(lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t | head -n 1)
    echo -e "  ${YELLOW}ℹ️  Backend ya está en ejecución en puerto ${BACKEND_PORT} (PID: ${EXISTING_BACKEND_PID}). Reutilizando...${NC}"
    echo "$EXISTING_BACKEND_PID" > "$BACKEND_PID_FILE"
else
    nohup "$VENV_UVICORN" backend.src.interfaces.api.main:create_app --factory --host 0.0.0.0 --port "$BACKEND_PORT" < /dev/null > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    disown "$BACKEND_PID" 2>/dev/null || true
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
    echo -e "  ⚡ Proceso backend iniciado con PID: ${BACKEND_PID}"

    # Esperar hasta 10 segundos a que el backend responda
    echo -n "  ⏳ Esperando salud de Backend API..."
    READY=false
    for i in {1..20}; do
        if curl -s "http://127.0.0.1:${BACKEND_PORT}/health" | grep -q '"status":' 2>/dev/null; then
            READY=true
            break
        fi
        sleep 0.5
        echo -n "."
    done
    echo ""

    if [ "$READY" = true ]; then
        echo -e "  ${GREEN}✓ Backend API operativo y saludable en http://localhost:${BACKEND_PORT}${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Backend inició pero aún no responde a /health. Revisa logs/backend.log si hay error.${NC}"
    fi
fi

# 7. Telemetry Ingestion Worker
echo -e "\n${BOLD}[3/5] Levantando Telemetry Ingestion Worker en Segundo Plano...${NC}"
WORKER_PID_FILE="$PROJECT_ROOT/.run/worker.pid"
WORKER_RUNNING=false

if [ -f "$WORKER_PID_FILE" ]; then
    OLD_PID=$(cat "$WORKER_PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "  ${YELLOW}ℹ️  Worker ya está en ejecución (PID: ${OLD_PID}).${NC}"
        WORKER_RUNNING=true
    fi
fi

if [ "$WORKER_RUNNING" = false ]; then
    nohup "$VENV_PYTHON" -m backend.src.infrastructure.queue.worker < /dev/null > "$PROJECT_ROOT/logs/worker.log" 2>&1 &
    WORKER_PID=$!
    disown "$WORKER_PID" 2>/dev/null || true
    echo "$WORKER_PID" > "$WORKER_PID_FILE"
    echo -e "  ${GREEN}✓ Worker iniciado con PID: ${WORKER_PID} (Logs: logs/worker.log)${NC}"
fi

# 8. Frontend SPA (Node dev.mjs)
echo -e "\n${BOLD}[4/5] Levantando Frontend Web SPA (Puerto ${FRONTEND_PORT})...${NC}"
FRONTEND_PID_FILE="$PROJECT_ROOT/.run/frontend.pid"

# Verificar compilación estática del frontend si falta dist
if [ ! -f "$PROJECT_ROOT/frontend/dist/index.html" ]; then
    echo -e "  📦 Dist del frontend no encontrada. Compilando aplicación..."
    (cd "$PROJECT_ROOT/frontend" && npm run build > "$PROJECT_ROOT/logs/frontend_build.log" 2>&1)
    echo -e "  ${GREEN}✓ Build del frontend completado.${NC}"
fi

if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null ; then
    EXISTING_FRONT_PID=$(lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t | head -n 1)
    echo -e "  ${YELLOW}ℹ️  Frontend ya está en ejecución en puerto ${FRONTEND_PORT} (PID: ${EXISTING_FRONT_PID}). Reutilizando...${NC}"
    echo "$EXISTING_FRONT_PID" > "$FRONTEND_PID_FILE"
else
    nohup node "$PROJECT_ROOT/frontend/dev.mjs" < /dev/null > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    disown "$FRONTEND_PID" 2>/dev/null || true
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    echo -e "  ⚡ Servidor frontend iniciado con PID: ${FRONTEND_PID}"

    # Esperar hasta 6 segundos
    echo -n "  ⏳ Esperando servidor frontend..."
    READY_FRONT=false
    for i in {1..12}; do
        if curl -s -I "http://127.0.0.1:${FRONTEND_PORT}/" | grep -q "200 OK" 2>/dev/null; then
            READY_FRONT=true
            break
        fi
        sleep 0.5
        echo -n "."
    done
    echo ""

    if [ "$READY_FRONT" = true ]; then
        echo -e "  ${GREEN}✓ Frontend SPA operativo en http://localhost:${FRONTEND_PORT}${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Frontend arrancó, revisa logs/frontend.log ante cualquier incidencia.${NC}"
    fi
fi

# 9. Túnel Público Seguro (Cloudflare Tunnel o ngrok)
echo -e "\n${BOLD}[5/5] Levantando Túnel Público HTTPS para Exposición en Línea...${NC}"
TUNNEL_PID_FILE="$PROJECT_ROOT/.run/tunnel.pid"
TUNNEL_URL_FILE="$PROJECT_ROOT/.run/tunnel_url.txt"
PUBLIC_URL=""

if [ "$START_TUNNEL" = true ]; then
    # Verificar si hay un túnel activo
    if [ -f "$TUNNEL_PID_FILE" ]; then
        OLD_TUNNEL_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$OLD_TUNNEL_PID" > /dev/null 2>&1; then
            if [ -f "$TUNNEL_URL_FILE" ]; then
                PUBLIC_URL=$(cat "$TUNNEL_URL_FILE")
            fi
            echo -e "  ${YELLOW}ℹ️  Túnel ya se encuentra activo (PID: ${OLD_TUNNEL_PID}).${NC}"
        fi
    fi

    if [ -z "$PUBLIC_URL" ]; then
        if command -v cloudflared &> /dev/null; then
            echo -e "  ⚡ Iniciando Cloudflare Quick Tunnel (HTTPS)..."
            nohup cloudflared tunnel --url "http://localhost:${FRONTEND_PORT}" < /dev/null > "$PROJECT_ROOT/logs/tunnel.log" 2>&1 &
            TUNNEL_PID=$!
            disown "$TUNNEL_PID" 2>/dev/null || true
            echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

            echo -n "  ⏳ Obteniendo dirección pública HTTPS segura..."
            for i in {1..30}; do
                sleep 0.5
                echo -n "."
                EXTRACTED=$(grep -E -o "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" "$PROJECT_ROOT/logs/tunnel.log" 2>/dev/null | head -n 1 || true)
                if [ -n "$EXTRACTED" ]; then
                    PUBLIC_URL="$EXTRACTED"
                    echo "$PUBLIC_URL" > "$TUNNEL_URL_FILE"
                    break
                fi
            done
            echo ""
        elif command -v ngrok &> /dev/null; then
            echo -e "  ⚡ Iniciando ngrok tunnel en puerto ${FRONTEND_PORT}..."
            nohup ngrok http "${FRONTEND_PORT}" --log=stdout < /dev/null > "$PROJECT_ROOT/logs/tunnel.log" 2>&1 &
            TUNNEL_PID=$!
            disown "$TUNNEL_PID" 2>/dev/null || true
            echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

            echo -n "  ⏳ Obteniendo dirección pública ngrok..."
            for i in {1..30}; do
                sleep 0.5
                echo -n "."
                EXTRACTED=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -n 1 | cut -d '"' -f 4 || true)
                if [ -z "$EXTRACTED" ]; then
                    EXTRACTED=$(grep -E -o "https://[a-zA-Z0-9.-]+\.ngrok-free\.app" "$PROJECT_ROOT/logs/tunnel.log" 2>/dev/null | head -n 1 || true)
                fi
                if [ -n "$EXTRACTED" ]; then
                    PUBLIC_URL="$EXTRACTED"
                    echo "$PUBLIC_URL" > "$TUNNEL_URL_FILE"
                    break
                fi
            done
            echo ""
        else
            echo -e "  ${YELLOW}⚠️  No se encontró 'cloudflared' ni 'ngrok' instalado.${NC}"
            echo "     Para habilitar el túnel público, instala cloudflared: brew install cloudflared"
        fi
    fi
else
    echo -e "  ${YELLOW}ℹ️  Flag --no-tunnel detectado. Saltando túnel público.${NC}"
fi

# 10. Resumen y URLs de acceso
echo -e "\n${CYAN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}🚀 ¡PÁRAMO URBANO ESTÁ 100% OPERATIVO Y EN LÍNEA!${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  🏠 ${BOLD}Frontend Local (SPA):${NC}    http://localhost:${FRONTEND_PORT}"
echo -e "  ⚙️  ${BOLD}Backend REST API:${NC}        http://localhost:${BACKEND_PORT}"
echo -e "  📖 ${BOLD}Documentación Swagger:${NC}   http://localhost:${BACKEND_PORT}/docs"

if [ -n "$PUBLIC_URL" ]; then
    echo -e "\n  🌐 ${GREEN}${BOLD}URL PÚBLICA EN LÍNEA (COMPARTIBLE):${NC}"
    echo -e "  👉 ${CYAN}${BOLD}${PUBLIC_URL}${NC}\n"
else
    echo -e "\n  ℹ️  ${YELLOW}Túnel no disponible o URL no resuelta aún.${NC}"
    echo -e "     Puedes revisar el log con: tail -f logs/tunnel.log\n"
fi

echo -e "------------------------------------------------------------"
echo -e "  📁 Directorio de PIDs:  .run/"
echo -e "  📜 Directorio de Logs:  logs/ (backend.log, frontend.log, worker.log, tunnel.log)"
echo -e "------------------------------------------------------------"
echo -e "  Comandos útiles:"
echo -e "    Consultar estado:  ${BOLD}./scripts/status.sh${NC}"
echo -e "    Reiniciar stack:   ${BOLD}./scripts/restart.sh${NC}"
echo -e "    Apagar stack:      ${BOLD}./scripts/stop.sh${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
