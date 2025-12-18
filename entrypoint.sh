#!/usr/bin/env sh
set -euo pipefail

if [ "${SEED_DATA:-true}" = "true" ]; then
  echo "Running seed..."
  python scripts/seed_insurance.py || echo "Seed failed, continuing: $?."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
