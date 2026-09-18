#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Script de Reinicio Unificado
# "Donde el asfalto toca la cumbre"
#
# Detiene limpiamente todo el stack y vuelve a iniciar todos los servicios y el túnel.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "\033[0;36m\033[1m🔄 Reiniciando el ecosistema de Páramo Urbano...\033[0m\n"

# 1. Ejecutar apagado ordenado
bash "$SCRIPT_DIR/stop.sh"

# 2. Breve pausa para asegurar liberación de sockets de red del kernel
sleep 2

# 3. Arrancar todo nuevamente
bash "$SCRIPT_DIR/start.sh" "$@"
