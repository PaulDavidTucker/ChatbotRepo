#!/bin/bash

# Run Django development server
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
daphne -p 8000 core.asgi:application
