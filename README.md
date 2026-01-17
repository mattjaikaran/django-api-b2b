# Django API Starter

A minimal Django API template built with [django-matt](https://github.com/mattjaikaran/django-matt).

## Features

- Django 5.2+ with async support
- JWT authentication out of the box
- Pydantic schemas for request/response validation
- OpenAPI documentation (Swagger & ReDoc)
- PostgreSQL database (SQLite option for development)
- Docker & Docker Compose
- uv package manager
- Comprehensive testing setup

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL (or use SQLite for development)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/django-api-starter.git myproject
cd myproject
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
# Or: uv pip install -e .
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Run migrations:
```bash
make migrate
# Or: python manage.py migrate
```

6. Create a superuser:
```bash
make superuser
# Or: python manage.py createsuperuser
```

7. Run the development server:
```bash
make run
# Or: python manage.py runserver
```

### With Docker

```bash
# Start database and cache
make docker-up

# Run migrations
make migrate

# Start development server
make run

# Or run everything in Docker
make docker-up-all
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user |
| PATCH | `/api/auth/me` | Update current user |
| POST | `/api/auth/change-password` | Change password |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

## Project Structure

```
├── apps/
│   ├── api.py              # API configuration
│   ├── core/               # Shared models and utilities
│   │   └── models.py       # Base models (TimestampMixin, etc.)
│   └── users/              # User app
│       ├── admin.py        # Admin configuration
│       ├── controllers.py  # API controllers
│       ├── models.py       # User model
│       └── schemas.py      # Pydantic schemas
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # URL configuration
│   ├── wsgi.py             # WSGI config
│   └── asgi.py             # ASGI config
├── tests/                  # Test files
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── manage.py
```

## Development

### Running Tests

```bash
make test
# Or: pytest -v
```

### Linting & Formatting

```bash
make lint    # Run linter
make format  # Format code
```

### Type Generation

Generate TypeScript types for your frontend:

```bash
make sync-types
# Or: python manage.py sync_types --target typescript --output ../frontend/src/types
```

## Deployment

### Environment Variables

See `.env.example` for all available configuration options.

Required for production:
- `SECRET_KEY` - Django secret key
- `DEBUG=False`
- `ALLOWED_HOSTS` - Your domain(s)
- Database credentials

### Docker Deployment

```bash
# Build production image
docker compose build

# Start all services
docker compose up -d
```

## License

MIT
