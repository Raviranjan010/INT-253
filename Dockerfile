# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN sh build.sh

RUN mkdir -p /app/media /app/data

EXPOSE 8000

CMD ["sh", "-c", "set -e; if [ \"${RUN_MIGRATIONS:-0}\" = 1 ]; then python manage.py migrate --noinput; fi; if [ \"${RUN_BOOTSTRAP:-0}\" = 1 ]; then python manage.py bootstrap_content; fi; exec gunicorn --bind 0.0.0.0:${PORT:-8000} --access-logfile - liveschool_project.wsgi:application"]

