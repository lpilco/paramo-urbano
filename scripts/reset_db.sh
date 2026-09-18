#!/usr/bin/env bash
# ==============================================================================
# Páramo Urbano (v2.0.0 Core) — Database Reset & Clean State Script
# Truncates all tables with cascade, runs migrations/schema creation from scratch,
# and ensures ZERO mock data or seeds remain in the database.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "🏔️  PÁRAMO URBANO — LIMPIEZA DE BASE DE DATOS (CLEAN STATE)"
echo "   Donde el asfalto toca la cumbre"
echo "============================================================"

cd "$ROOT_DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python3 scripts/reset_db.py

echo ""
echo "✅ Base de datos purgada a estado 100% limpio."
echo "   Tablas listas para registrar el primer usuario real en: /#/register"
echo "============================================================"
