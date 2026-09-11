# Marginalia — Backend

A private reading journal API. Marginalia lets readers track what they're reading, hold onto the passages and quotes that stopped them mid-page, and get a personal year-end reflection on their reading — a "Year in Books."

**Live API:** https://marginalia-backend-ygk4.onrender.com
**Frontend:** https://marginalia-online.vercel.app

---

## Tech Stack

- **Framework:** Django + Django REST Framework
- **Auth:** SimpleJWT (access/refresh token pattern)
- **Database:** PostgreSQL (Neon, serverless) in production, SQLite for local dev
- **Static files:** WhiteNoise
- **Hosting:** Render
- **CORS:** django-cors-headers

---

## Features

- Custom user signup/login (separate steps — signup does not auto-issue tokens)
- JWT access/refresh authentication with token refresh endpoint
- Book CRUD, scoped per-user, grouped by reading status (`want_to_read` / `reading` / `read`)
- Ownership isolation: requesting another user's book/note returns `404`, never `403`
- Nested Notes & Quotes per book, chronological (oldest-first) ordering
- Cover search proxy against Open Library, with clean empty-array fallback (no error) when no match is found
- Year in Books stats endpoint: total books/pages read, favorite genre, longest book, most-quoted book, reading streak — all computed server-side for the current year

---

## Local Setup

```bash
git clone <repo-url>
cd marginalia_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SECRET_KEY=your-local-dev-secret-key
DEBUG=True
ALLOWED_HOSTS=
DATABASE_URL=
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=
```

Leaving `DATABASE_URL` blank is intentional — the app falls back to local SQLite automatically when it's empty. You do not need a local Postgres instance to develop.

```bash
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://localhost:8000`. The frontend's `NEXT_PUBLIC_API_URL` should point here for local development.

---

## Environment Variables (Production / Render)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key — unique per environment, never shared with local |
| `DEBUG` | `False` in production |
| `DATABASE_URL` | Neon Postgres connection string |
| `ALLOWED_HOSTS` | The real deployed backend hostname (no scheme, e.g. `marginalia-backend-ygk4.onrender.com`) |
| `CORS_ALLOWED_ORIGINS` | The real deployed **frontend** URL (e.g. `https://marginalia-online.vercel.app`) |
| `CSRF_TRUSTED_ORIGINS` | The real deployed **backend's own** URL (needed for Django admin login, since that's the only session/cookie-based auth in this stack) |
| `DJANGO_SUPERUSER_USERNAME` / `EMAIL` | Used once by `build.sh` to auto-create an admin account on first deploy |
| `DJANGO_SUPERUSER_PASSWORD` | Same as above — set temporarily for first deploy, then removed from the dashboard once admin login is confirmed working (the account persists in the database regardless) |

`settings.py` also sets `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` as a fixed code line (not an env var) — required for Django to correctly recognize HTTPS requests behind Render's reverse proxy.

---

## Deployment (Render)

- **Build Command:** `./build.sh` (installs dependencies, runs `collectstatic`, runs `migrate`, conditionally creates the superuser)
- **Start Command:** `gunicorn marginalia_backend.wsgi:application`
- Database is a separate Neon Postgres project, connected via `DATABASE_URL`

---

## API Reference

All authenticated endpoints require `Authorization: Bearer <access_token>`.

### Auth

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/api/auth/signup/` | `{ username, email, password }` → `201`, no tokens issued |
| POST | `/api/auth/login/` | `{ username, password }` → `{ access, refresh }` |
| POST | `/api/auth/refresh/` | `{ refresh }` → `{ access }` |
| GET | `/api/auth/me/` | Returns the authenticated user's `{ id, username, email }` |

### Books

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/books/` | Plain array, no pagination. Optional `?status=` filter |
| POST | `/api/books/` | Create — `title`/`author` required, `cover_color` always required (never null) |
| GET / PATCH / PUT / DELETE | `/api/books/<id>/` | Scoped to owner — 404 if not owned/found |

### Notes & Quotes

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/books/<book_id>/notes/` | Plain array, ordered oldest-first |
| POST | `/api/books/<book_id>/notes/` | `{ content, entry_type: "note"\|"quote" }` |
| PATCH / PUT / DELETE | `/api/books/<book_id>/notes/<note_id>/` | Scoped to owner |

### Cover Search

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/books/cover-search/?q=<query>` | Proxies Open Library. Empty `results` array on no match — not an error |

### Year in Books

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/wrapup/` | Defaults to current year. Nested book objects are `null` (not present) when nothing qualifies |

---

## Notes on Design Decisions

- Signup and login are deliberately separate — no auto-login after account creation.
- List endpoints are intentionally unpaginated; payloads are small even at 50+ books.
- 404-not-403 on all ownership checks prevents leaking whether a resource exists to a non-owner.

