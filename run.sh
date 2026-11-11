#!/bin/sh
# Запуск: ./run.sh [опции]
ROOT=$(cd "$(dirname "$0")" && pwd)
PYTHONPATH="$ROOT/src" exec "${PYTHON:-python3}" -m depviz "$@"
