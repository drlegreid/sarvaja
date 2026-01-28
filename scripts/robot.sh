#!/bin/bash
# Robot Framework Test Runner
# Per RF-001: E2E Test Automation
# Per TEST-BDD-01-v1: BDD E2E Testing Standard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ROBOT_DIR="${PROJECT_ROOT}/tests/e2e/robot"
RESULTS_DIR="${ROBOT_DIR}/results"

# Default settings
INCLUDE_TAG="${ROBOT_INCLUDE_TAG:-smoke}"
BROWSER="${ROBOT_BROWSER:-chromium}"
HEADLESS="${ROBOT_HEADLESS:-True}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG      Include tests with tag (default: smoke)"
    echo "  -s, --suite SUITE  Run specific suite file"
    echo "  -b, --browser BROWSER  Browser to use (chromium, firefox, webkit)"
    echo "  --headed           Run browser in headed mode"
    echo "  --api-only         Run only API tests (no browser)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run smoke tests"
    echo "  $0 -t api              # Run API tests only"
    echo "  $0 -t ui --headed      # Run UI tests with visible browser"
    echo "  $0 -s smoke.robot      # Run specific suite"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            INCLUDE_TAG="$2"
            shift 2
            ;;
        -s|--suite)
            SUITE="$2"
            shift 2
            ;;
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        --headed)
            HEADLESS="False"
            shift
            ;;
        --api-only)
            INCLUDE_TAG="api"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Ensure results directory exists
mkdir -p "${RESULTS_DIR}"

# Build robot command
ROBOT_CMD="robot"
ROBOT_CMD="${ROBOT_CMD} --outputdir ${RESULTS_DIR}"
ROBOT_CMD="${ROBOT_CMD} --variable BROWSER:${BROWSER}"
ROBOT_CMD="${ROBOT_CMD} --variable HEADLESS:${HEADLESS}"
ROBOT_CMD="${ROBOT_CMD} --include ${INCLUDE_TAG}"

# Add suite if specified
if [[ -n "${SUITE}" ]]; then
    SUITE_PATH="${ROBOT_DIR}/suites/${SUITE}"
else
    SUITE_PATH="${ROBOT_DIR}/suites"
fi

echo -e "${GREEN}Running Robot Framework tests...${NC}"
echo "Include tag: ${INCLUDE_TAG}"
echo "Browser: ${BROWSER}"
echo "Headless: ${HEADLESS}"
echo "Suite: ${SUITE_PATH}"
echo ""

# Run tests
${ROBOT_CMD} "${SUITE_PATH}"
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed. See ${RESULTS_DIR}/report.html for details.${NC}"
fi

exit $EXIT_CODE
