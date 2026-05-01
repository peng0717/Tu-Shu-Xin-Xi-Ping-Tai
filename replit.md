# 图书信息一体化平台 (Integrated Library Information Platform)

## Overview

A full-stack library management system built with Flask. It provides a web-based admin dashboard for managing books, users, borrowing records, reservations, and announcements.

## Tech Stack

- **Backend**: Python / Flask 2.3.3
- **Database**: SQLite (library.db)
- **Authentication**: JWT (PyJWT)
- **Frontend**: Jinja2 templates + Bootstrap 5
- **Mobile**: WeChat Mini Program (in `miniprogram/` directory)

## Project Structure

```
app.py              # Flask entry point and web admin routes
config.py           # Configuration (DB path, JWT settings, etc.)
models.py           # SQLite connection and DB initialization
init_db.py          # Database seeding script (run once)
requirements.txt    # Python dependencies
routes/             # Flask blueprints for API endpoints
  auth.py           # Authentication (login/register)
  books.py          # Book management
  borrow.py         # Borrow/return/renew logic
  reservation.py    # Book reservations
  stats.py          # Dashboard statistics
  notice.py         # System announcements
utils/
  auth.py           # JWT decorator
  isbn_query.py     # Douban API ISBN lookup
templates/          # Jinja2 HTML templates
  index.html        # Landing page
  admin/            # Admin panel pages
miniprogram/        # WeChat Mini Program source
```

## Running the App

```bash
pip install -r requirements.txt
python init_db.py   # Only needed once
python app.py       # Starts on port 5000
```

## Default Credentials

- Admin: `admin` / `admin123`
- Teacher: `T001` / `123456`
- Student: `S2024001` / `123456`

## API Endpoints

- `/api/auth` — Authentication
- `/api/books` — Book management
- `/api/borrow` — Borrow/return operations
- `/api/reservation` — Reservations
- `/api/stats` — Statistics
- `/api/notice` — Announcements
- `/api/health` — Health check

## Web Admin Routes

- `/` — Landing page
- `/admin` — Admin dashboard (requires login)
- `/admin/login` — Admin login
- `/admin/books` — Book management
- `/admin/borrows` — Borrow management
- `/admin/users` — User management
- `/admin/notices` — Announcement management
- `/admin/reservations` — Reservation management
- `/admin/stats` — Statistics & reports

## Deployment

Configured for autoscale deployment using Gunicorn:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```
