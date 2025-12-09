## AIRPORT API
-- ---

 API service for airport management written on DRF

-----
### Installing using GitHub
- Install PostgreSQL and create db
```bash
git clone https://github.com/0lex1y/airport_service.git
cd app/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py loaddata airport_data.json
python manage.py migrate
python manage.py runserver
```


### Run with Docker 
---- -
- Docker should be installed
```bash
- docker compose build
- docker compose up
```
### Getting access
----- - 

- create user via /api/user/register
- get access token via /api/user/token

### Features
- JWT auth
- Admin panel /admin/
- **OpenAPI documentation** (`/api/docs/`)
- Flight search with filters (date, departure/arrival airport, availability)
- Multi-ticket booking in a single atomic transaction
- Seat collision protection (cannot book the same seat twice)
- Aircraft scheduling conflict validation
- **Seat map endpoint** — `/api/flights/{id}/seats/`
- Airplane image upload (admin only)
- Order filtering by status!

### Tech Stack
--- - 
- Python 3.11
- Django 5.0 + Django REST Framework
- PostgreSQL
- drf-spectacular (OpenAPI 3)
- SimpleJWT
- Pillow (image processing)
- Docker & docker-compose

![Diagram](https://github.com/0lex1y/airport_service/blob/develop/img.png?raw=true)
