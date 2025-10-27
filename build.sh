#!/bin/bash
set -e

echo "Building Chatbot Widget..."

# Build the React widget
cd chatbot-widget
npm install
npm run build
npm run build-widget

# Copy widget to Django static files
cd ..
mkdir -p backend/static/chatbot/js
cp chatbot-widget/dist/chatbot-widget.js backend/static/chatbot/js/

echo "Building Django assets..."
cd backend

# Run Django commands
python manage.py collectstatic --noinput
python manage.py migrate

echo "Build complete!"
