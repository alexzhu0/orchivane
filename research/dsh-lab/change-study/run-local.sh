#!/bin/sh
set -eu
STUDY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN="$STUDY_DIR/../.venv-dsh/bin/python"
exec "$PYTHON_BIN" "$STUDY_DIR/strict_experiment.py" "$@"
