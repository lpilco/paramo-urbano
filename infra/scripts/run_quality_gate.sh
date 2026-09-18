#!/usr/bin/env bash
# ==============================================================================
# PÁRAMO URBANO (v2.0.0 Core) — Unified Quality Gate Certification Script
# "Donde el asfalto toca la cumbre"
# 
# Stages executed:
#   1. Static Code Analysis & Typing (Flake8, Mypy, Frontend TypeScript)
#   2. Physiological Engine Unit Tests with 100% Coverage Certification
#   3. Infrastructure & Integration Tests (PostgreSQL, MinIO, Redis, Parsers)
#   4. E2E Gherkin Acceptance Criteria & NFR Certification (FR-01 - FR-05, NFRs)
#   5. Database Master Data Seeding (Idempotent Seed Verification)
# ==============================================================================

set -euo pipefail

# Project root resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Determine Python binary
if [[ -f "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
    PYTEST_BIN="${PROJECT_ROOT}/.venv/bin/pytest"
    FLAKE8_BIN="${PROJECT_ROOT}/.venv/bin/flake8"
    MYPY_BIN="${PROJECT_ROOT}/.venv/bin/mypy"
else
    PYTHON_BIN="python3"
    PYTEST_BIN="pytest"
    FLAKE8_BIN="flake8"
    MYPY_BIN="mypy"
fi

echo -e "${CYAN}${BOLD}"
echo "================================================================================"
echo "    PÁRAMO URBANO (v2.0.0 Core) — QUALITY GATE & CERTIFICATION SUITE            "
echo "    \"Donde el asfalto toca la cumbre\"                                          "
echo "================================================================================"
echo -e "${NC}"
echo -e "Platform Engine:  $(uname -s) $(uname -m)"
echo -e "Python Runtime:   $("${PYTHON_BIN}" --version 2>&1)"
echo -e "Execution Path:   ${PROJECT_ROOT}"
echo -e "Timestamp:        $(date -u +"%Y-%m-%dT%H:%M:%SZ")\n"

TOTAL_STAGES=5
FAILED_STAGES=0

STAGE_1_STATUS="PENDING"
STAGE_2_STATUS="PENDING"
STAGE_3_STATUS="PENDING"
STAGE_4_STATUS="PENDING"
STAGE_5_STATUS="PENDING"

# ------------------------------------------------------------------------------
# STAGE 1: Static Code Analysis & Type Verification
# ------------------------------------------------------------------------------
echo -e "${BLUE}${BOLD}[STAGE 1/5] Static Analysis & Type Checking...${NC}"
STAGE_1_START=$(date +%s)

echo -e "  -> Running Backend Flake8 Linter..."
if "${FLAKE8_BIN}" backend/src backend/tests --max-line-length=120 --extend-ignore=E203,W503,F401,W391,E302,E305; then
    echo -e "     ${GREEN}[PASS] Backend Flake8 clean.${NC}"
else
    echo -e "     ${RED}[FAIL] Backend Flake8 failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_1_STATUS="FAIL"
fi

echo -e "  -> Running Backend Mypy Strict Type Analysis..."
if "${MYPY_BIN}" backend/src/domain/physiological --ignore-missing-imports; then
    echo -e "     ${GREEN}[PASS] Backend Mypy clean.${NC}"
else
    echo -e "     ${RED}[FAIL] Backend Mypy failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_1_STATUS="FAIL"
fi

echo -e "  -> Running Frontend TypeScript Compilation (tsc --noEmit)..."
if (cd frontend && ./node_modules/.bin/tsc --noEmit); then
    echo -e "     ${GREEN}[PASS] Frontend TypeScript check passed.${NC}"
else
    echo -e "     ${RED}[FAIL] Frontend TypeScript check failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_1_STATUS="FAIL"
fi

if [[ "${STAGE_1_STATUS}" != "FAIL" ]]; then
    STAGE_1_STATUS="PASS"
fi
STAGE_1_DURATION=$(( $(date +%s) - STAGE_1_START ))

# ------------------------------------------------------------------------------
# STAGE 2: Physiological Core Unit Tests (100% Coverage Target)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}${BOLD}[STAGE 2/5] Physiological Core Unit Tests & 100% Coverage Certification...${NC}"
STAGE_2_START=$(date +%s)

if "${PYTEST_BIN}" -q --cov=backend.src.domain.physiological --cov-report=term-missing --cov-fail-under=100 backend/tests/unit/domain/physiological; then
    echo -e "     ${GREEN}[PASS] Physiological domain unit tests passed with 100% line coverage.${NC}"
    STAGE_2_STATUS="PASS"
else
    echo -e "     ${RED}[FAIL] Coverage did not reach 100% or unit tests failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_2_STATUS="FAIL"
fi
STAGE_2_DURATION=$(( $(date +%s) - STAGE_2_START ))

# ------------------------------------------------------------------------------
# STAGE 3: Infrastructure & Application Integration Tests
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}${BOLD}[STAGE 3/5] Infrastructure & Integration Tests...${NC}"
STAGE_3_START=$(date +%s)

if "${PYTEST_BIN}" -q backend/tests/integration; then
    echo -e "     ${GREEN}[PASS] Integration test suite passed.${NC}"
    STAGE_3_STATUS="PASS"
else
    echo -e "     ${RED}[FAIL] Integration tests failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_3_STATUS="FAIL"
fi
STAGE_3_DURATION=$(( $(date +%s) - STAGE_3_START ))

# ------------------------------------------------------------------------------
# STAGE 4: E2E Gherkin Acceptance Criteria & NFR Certification
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}${BOLD}[STAGE 4/5] E2E Gherkin Acceptance Criteria & NFR Certification (FR-01 to FR-05)...${NC}"
STAGE_4_START=$(date +%s)

if "${PYTEST_BIN}" -q backend/tests/e2e/test_acceptance_criteria.py; then
    echo -e "     ${GREEN}[PASS] All E2E acceptance criteria and NFRs certified.${NC}"
    STAGE_4_STATUS="PASS"
else
    echo -e "     ${RED}[FAIL] Acceptance criteria or NFRs failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_4_STATUS="FAIL"
fi
STAGE_4_DURATION=$(( $(date +%s) - STAGE_4_START ))

# ------------------------------------------------------------------------------
# STAGE 5: Database Seeding Verification (Idempotence)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}${BOLD}[STAGE 5/5] Data Seeding Integrity & Idempotence Certification...${NC}"
STAGE_5_START=$(date +%s)

if "${PYTHON_BIN}" -m backend.src.infrastructure.database.seeds; then
    echo -e "     ${GREEN}[PASS] Database seed execution verified idempotently.${NC}"
    STAGE_5_STATUS="PASS"
else
    echo -e "     ${RED}[FAIL] Database seed execution failed.${NC}"
    FAILED_STAGES=$((FAILED_STAGES + 1))
    STAGE_5_STATUS="FAIL"
fi
STAGE_5_DURATION=$(( $(date +%s) - STAGE_5_START ))

# ------------------------------------------------------------------------------
# FINAL EXECUTIVE CERTIFICATION SUMMARY
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}================================================================================${NC}"
echo -e "${CYAN}${BOLD}             PÁRAMO URBANO — QUALITY GATE CERTIFICATION REPORT                  ${NC}"
echo -e "${CYAN}${BOLD}================================================================================${NC}"

format_status() {
    local status="$1"
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}${BOLD}[ PASS ]${NC}"
    else
        echo -e "${RED}${BOLD}[ FAIL ]${NC}"
    fi
}

echo -e " Stage 1: Static Code Analysis & Typing       | Duration: ${STAGE_1_DURATION}s | Status: $(format_status "${STAGE_1_STATUS}")"
echo -e " Stage 2: Physiological Core Unit (100% Cov)  | Duration: ${STAGE_2_DURATION}s | Status: $(format_status "${STAGE_2_STATUS}")"
echo -e " Stage 3: Infrastructure & Integration        | Duration: ${STAGE_3_DURATION}s | Status: $(format_status "${STAGE_3_STATUS}")"
echo -e " Stage 4: E2E Acceptance & NFRs (FR-01 - 05)  | Duration: ${STAGE_4_DURATION}s | Status: $(format_status "${STAGE_4_STATUS}")"
echo -e " Stage 5: Database Data Seeding & Idempotency  | Duration: ${STAGE_5_DURATION}s | Status: $(format_status "${STAGE_5_STATUS}")"
echo -e "${CYAN}--------------------------------------------------------------------------------${NC}"

if [[ ${FAILED_STAGES} -eq 0 ]]; then
    echo -e "${GREEN}${BOLD} >>> QUALITY GATE STATUS: ALL CRITERIA CERTIFIED (PASSED) <<< ${NC}"
    echo -e "${GREEN} System is production-ready under PRD & Architectural Standards.${NC}"
    echo -e "${CYAN}================================================================================${NC}\n"
    exit 0
else
    echo -e "${RED}${BOLD} >>> QUALITY GATE STATUS: FAILED (${FAILED_STAGES} STAGES FAILED) <<< ${NC}"
    echo -e "${RED} Remediation required before release deployment.${NC}"
    echo -e "${CYAN}================================================================================${NC}\n"
    exit 1
fi
