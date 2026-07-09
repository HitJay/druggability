#!/bin/bash
# Quick launcher for scaffold clustering
# Run: bash /das/user/QYJI/druggability/scripts/run_scaffold_venv.sh
VENV_PYTHON="/usr/bin/python3.12"
SCRIPT="/das/user/QYJI/druggability/scripts/scaffold_clustering.py"
export PYTHONPATH="/home/QYJI/das/druggability/.venv/lib/python3.12/site-packages:$PYTHONPATH"
exec "$VENV_PYTHON" "$SCRIPT"
