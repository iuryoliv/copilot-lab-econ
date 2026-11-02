#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.lock.txt -e '.[test]'
.venv/bin/python -m pip check
if [ ! -f data/raw/catalog.json ]; then
  .venv/bin/python -m econlab.cli download
fi
.venv/bin/python -m econlab.cli reset
