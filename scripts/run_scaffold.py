#!/usr/bin/env python3
"""Bootstrap script to run scaffold_clustering.py via the target venv."""
import subprocess
import sys

venv_python = "/home/QYJI/das/druggability/.venv/bin/python3"
script = "/das/user/QYJI/druggability/scripts/scaffold_clustering.py"

result = subprocess.run([venv_python, script], capture_output=True, text=True, cwd="/das/user/QYJI/druggability")
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
