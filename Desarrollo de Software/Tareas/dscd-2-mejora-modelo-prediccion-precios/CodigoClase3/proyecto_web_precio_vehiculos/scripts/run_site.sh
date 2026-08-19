#!/usr/bin/env bash
set -euo pipefail

trap 'kill 0' EXIT

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$script_dir/run_frontend.sh" &
bash "$script_dir/run_backend.sh"
