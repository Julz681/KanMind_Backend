# KanMind Backend (Django + DRF)

KanMind is a simple **Kanban** backend built with **Django** and **Django REST Framework**.  
It provides a clean REST API (JSON) that supports user authentication, board/column/ticket
management, and can be consumed by any frontend (e.g. the provided Vanilla-JS frontend).

---

## Features
- **Authentication**
  - User signup & login with JWT (access & refresh tokens)
  - Guest login for quick demo accounts
  - Token refresh endpoint
- **Kanban**
  - Boards with members (owner + invited users)
  - Columns with ordering
  - Tickets with priority, due date, assignee and drag-and-drop style positioning
- **Permissions**
  - Owners can create/update/delete boards
  - Members can view boards and work with columns/tickets inside shared boards
- **Admin Interface** (`/admin/`) to inspect or edit all data
- **CORS enabled** for local frontend development

---

## Project Structure
KANMIND/
├─ core/                 # Django project (settings, urls, wsgi)
├─ auth_app/             # Authentication logic
│   └─ api/              # serializers, views, urls, permissions
├─ kanban_app/           # Kanban boards, columns, tickets
│   └─ api/              # serializers, views, urls, permissions
├─ manage.py
├─ requirements.txt
└─ README.md

---

## Requirements
- Python **3.10+**
- pip / venv
- SQLite (default) or another Django-supported DB if you configure it

---

## Setup

Clone the repository and create a virtual environment:

git clone 
cd kanmind-backend

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run database migrations and create an optional superuser for the admin site:

python manage.py migrate
python manage.py createsuperuser   # optional but useful

Start the development server:

python manage.py runserver

The API is now available at:  
http://127.0.0.1:8000/

---

## API Overview

All Kanban endpoints require authentication:
Authorization: Bearer <access_token>

### Auth Endpoints
Method | URL | Description
------ | --- | -----------
POST | /api/auth/signup/ | Create a new user account
POST | /api/auth/login/ | Obtain access & refresh tokens
POST | /api/auth/token/refresh/ | Get a new access token using a refresh token
POST | /api/auth/guest-login/ | Create/obtain a guest user and tokens

### Kanban Endpoints
Method | URL | Description
------ | --- | -----------
GET / POST | /api/kanban/boards/ | List or create boards
GET / PATCH / DELETE | /api/kanban/boards/{id}/ | Retrieve, update or delete a board
GET / POST | /api/kanban/columns/ | List or create columns
GET / PATCH / DELETE | /api/kanban/columns/{id}/ | Retrieve, update or delete a column
GET / POST | /api/kanban/tickets/ | List or create tickets
GET / PATCH / DELETE | /api/kanban/tickets/{id}/ | Retrieve, update or delete a ticket

Example request (create a board):

POST /api/kanban/boards/
Content-Type: application/json
Authorization: Bearer <access_token>

{ "title": "My first board" }

---

## Running Tests

The project includes API tests covering authentication, board permissions,
and CRUD operations.

Run all tests:

python manage.py test

Optional coverage report:

pip install coverage
coverage run manage.py test
coverage report -m

---

## Deployment Notes
- For production, set DEBUG = False and configure
  ALLOWED_HOSTS, database and DJANGO_SECRET_KEY via environment variables.
- Adjust CORS settings in core/settings.py (currently open for development).

---

