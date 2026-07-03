# Spark

Generate and run production-ready async FastAPI projects.

## Quick start

```bash
mkdir my-api && cd my-api
spark create
spark dev
```

## What it generates

- **FastAPI** app with async SQLAlchemy + asyncpg
- **JWT auth** with refresh token rotation and argon2 password hashing
- **Alembic** migrations (async)
- **Redis** for token blacklisting
- **CORS**, request logging middleware, Rich-formatted logging
- **process-compose** runner for local dev (uvicorn + redis)

## Commands

| Command        | Description                                    |
|----------------|------------------------------------------------|
| `spark create` | Scaffold a complete FastAPI project in cwd     |
| `spark dev`    | Start the project (process-compose up)         |
