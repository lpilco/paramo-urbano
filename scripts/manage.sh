#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Gestor Central CLI
# "Donde el asfalto toca la cumbre"
#
# Uso:
#   ./scripts/manage.sh start     # Inicia todos los servicios y el túnel
#   ./scripts/manage.sh stop      # Detiene servidores y túnel
#   ./scripts/manage.sh restart   # Reinicia todo el entorno
#   ./scripts/manage.sh status    # Muestra el estado del sistema y la URL pública
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMMAND="${1:-status}"
shift || true

case "$COMMAND" in
    start|up)
        bash "$SCRIPT_DIR/start.sh" "$@"
        ;;
    stop|down)
        bash "$SCRIPT_DIR/stop.sh" "$@"
        ;;
    restart)
        bash "$SCRIPT_DIR/restart.sh" "$@"
        ;;
    status|ps)
        bash "$SCRIPT_DIR/status.sh" "$@"
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status} [opciones]"
        echo ""
        echo "Comandos disponibles:"
        echo "  start     Levanta la base de datos, backend, worker, frontend y túnel público HTTPS"
        echo "  stop      Detiene servidores y túnel (usa --all para detener también Docker)"
        echo "  restart   Reinicia ordenadamente todos los servicios y el túnel"
        echo "  status    Consulta el estado y muestra las URLs locales y públicas"
        exit 1
        ;;
esac
