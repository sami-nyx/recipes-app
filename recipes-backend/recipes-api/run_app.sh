#!/usr/bin/env bash
set -euo pipefail

set -a
source .env
set +a

exec gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  'app:create_app()'