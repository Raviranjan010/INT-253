#!/bin/sh
set -eu
python -m pip install --no-cache-dir -r requirements.txt
DEBUG=True STATIC_MANIFEST=1 python manage.py collectstatic --noinput
