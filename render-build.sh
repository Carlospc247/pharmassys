#!/usr/bin/env bash
# Parar a execução se der erro
set -o errexit

# Rodar migrações e coletar estáticos
python manage.py migrate
python manage.py collectstatic --noinput

# Iniciar o servidor
gunicorn pharmassys.wsgi:application --bind 0.0.0.0:$PORT
