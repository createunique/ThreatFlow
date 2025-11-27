#!/bin/bash
#
# ThreatFlow Test Runner
# Runs comprehensive tests for workflow execution
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           ThreatFlow Comprehensive Test Runner           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-timeout"
    exit 1
fi

# Check middleware health
check_middleware() {
    echo -e "${YELLOW}Checking middleware health...${NC}"
    MIDDLEWARE_URL="${MIDDLEWARE_URL:-http://localhost:8030}"
    
    if curl -s "${MIDDLEWARE_URL}/health/" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Middleware is running at ${MIDDLEWARE_URL}${NC}"
        return 0
    else
        echo -e "${RED}✗ Middleware not responding at ${MIDDLEWARE_URL}${NC}"
        return 1
    fi
}

# Run unit tests (no external services needed)
run_unit_tests() {
    echo -e "\n${BLUE}═══ Running Unit Tests ═══${NC}"
    pytest "${SCRIPT_DIR}/test_distribution_logic.py" -v --tb=short "$@"
}

# Run integration tests (require middleware)
run_integration_tests() {
    echo -e "\n${BLUE}═══ Running Integration Tests ═══${NC}"
    
    if ! check_middleware; then
        echo -e "${YELLOW}Skipping integration tests - middleware not available${NC}"
        return 0
    fi
    
    pytest "${SCRIPT_DIR}/test_linear_workflows.py" \
           "${SCRIPT_DIR}/test_conditional_workflows.py" \
           "${SCRIPT_DIR}/test_combined_workflows.py" \
           "${SCRIPT_DIR}/test_api_integration.py" \
           -v --tb=short "$@"
}

# Run specific test file
run_specific() {
    echo -e "\n${BLUE}═══ Running Specific Tests ═══${NC}"
    pytest "$@"
}

# Print usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all          Run all tests (unit + integration)"
    echo "  unit         Run unit tests only (no external services)"
    echo "  integration  Run integration tests only (requires middleware)"
    echo "  linear       Run linear workflow tests"
    echo "  conditional  Run conditional workflow tests"
    echo "  combined     Run combined/complex workflow tests"
    echo "  api          Run API integration tests"
    echo "  file <path>  Run specific test file"
    echo ""
    echo "Options:"
    echo "  -v, --verbose    Verbose output"
    echo "  -s               Show print statements"
    echo "  -k <pattern>     Run tests matching pattern"
    echo "  --tb=<style>     Traceback style (short, long, no)"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run all tests"
    echo "  $0 unit                   # Run unit tests only"
    echo "  $0 conditional -v -s      # Run conditional tests with verbose output"
    echo "  $0 file test_linear.py    # Run specific test file"
    echo ""
}

# Main script
case "${1:-all}" in
    all)
        shift || true
        run_unit_tests "$@"
        run_integration_tests "$@"
        ;;
    unit)
        shift || true
        run_unit_tests "$@"
        ;;
    integration)
        shift || true
        run_integration_tests "$@"
        ;;
    linear)
        shift || true
        check_middleware && pytest "${SCRIPT_DIR}/test_linear_workflows.py" -v "$@"
        ;;
    conditional)
        shift || true
        check_middleware && pytest "${SCRIPT_DIR}/test_conditional_workflows.py" -v "$@"
        ;;
    combined)
        shift || true
        check_middleware && pytest "${SCRIPT_DIR}/test_combined_workflows.py" -v "$@"
        ;;
    api)
        shift || true
        check_middleware && pytest "${SCRIPT_DIR}/test_api_integration.py" -v "$@"
        ;;
    file)
        shift
        run_specific "$@"
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}═══ Test Run Complete ═══${NC}"
