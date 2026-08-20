#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/.." && pwd)"

cd "$project_dir"
uvicorn app.main:app --host 0.0.0.0 --port 9011 --reload
