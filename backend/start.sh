#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
daphne -p 8000 -b 0.0.0.0 core.asgi:application
