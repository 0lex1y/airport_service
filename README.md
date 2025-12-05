AIRPORT API
 API service for airport management written on DRF

Installing using GitHub
Install PostgreSQL and create db
git clone https://github.com/0lex1y/airport_service.git
cd app/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
set DB_HOST
set DB_PASSWORD
set DB_NAME
set DB_USER
set SECRET_KEY=
python manage.py migrate
python manage.py runserver

Run with Docker 
Docker should be installed
docker compose build
docker compose up

Getting access
create user via /api/user/register
get access token via /api/user/token

Features
JWT auth
Admin panel /admin/
Documentation is located at /api/doc/swagger/
Managing order and tickets
...
...
...
...
