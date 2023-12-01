#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py makemigrations
python manage.py migrate
python manage.py images_api_app_setup_testusers
python manage.py runserver 0.0.0.0:8000
