#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
python manage.py makemigrations interface
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python create_superuser.py

# Start server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000 