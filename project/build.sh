#!/usr/bin/env bash
# Render build command: bash build.sh (Root Directory: project)
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements-render.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
