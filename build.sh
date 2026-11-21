#!/usr/bin/env bash
# Run on the hosting platform's build step (e.g. Render).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_menu
