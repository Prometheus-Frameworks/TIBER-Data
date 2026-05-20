#!/usr/bin/env bash
set -euo pipefail

SKIP_PYTHON_TESTS="${SKIP_PYTHON_TESTS:-0}"

if [[ "$SKIP_PYTHON_TESTS" == "1" ]]; then
  echo "SKIP_PYTHON_TESTS=1 set; skipping python test suite intentionally."
else
  if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: python is required for pre-PR validation. Install Python or set SKIP_PYTHON_TESTS=1 to intentionally skip." >&2
    exit 1
  fi

  if ! python -c "import pytest" >/dev/null 2>&1; then
    echo "ERROR: pytest is required for pre-PR validation. Install test dependencies or set SKIP_PYTHON_TESTS=1 to intentionally skip." >&2
    exit 1
  fi
fi

echo "Running TypeScript checks..."
npm run typecheck
npm run test

if [[ "$SKIP_PYTHON_TESTS" != "1" ]]; then
  echo "Running Python tests..."
  python -m pytest
fi

echo "All pre-PR checks passed."
