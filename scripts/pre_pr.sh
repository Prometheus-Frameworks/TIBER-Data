#!/usr/bin/env bash
set -euo pipefail

printf '\n[TIBER pre_pr] Starting deterministic pre-PR checks...\n'

printf '\n1) Typecheck\n'
npm run typecheck

printf '\n2) Test\n'
npm run test

printf '\n[TIBER pre_pr] All checks passed.\n'
