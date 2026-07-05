# Spark — Code Critique

## Overview

Comprehensive review of the spark scaffolding tool across security, error handling, logging, and architecture. Based on the actual source files in `spark/`, scaffold templates in `spark/scaffold/`, and test suite in `tests/`.

---

## Security

### Critical

| Issue | File | Detail |
|---|---|---|
| Hardcoded CORS origin | `spark/scaffold/app/main.py.tpl:28` | `origins = ["http://localhost:5173"]` is hardcoded. Should be read from `CORS_ORIGINS` env var (comma-separated) with a sensible default. |
| `SECRET_KEY` crash on missing env var | `spark/scaffold/app/core/auth.py.tpl:25` | `os.environ["SECRET_KEY"]` raises unhandled `KeyError` if not set. Use `os.getenv("SECRET_KEY")` and validate at startup with a clear error message and graceful exit. |
| Malformed DB URL on missing env vars | `spark/scaffold/app/core/database.py.tpl:9` | `os.getenv("DB_PASSWORD")` can return `None`, producing `None` in the connection string (e.g., `postgresql+asyncpg://user:None@localhost:5432/db`). Validate all required vars before constructing URL or fail early. |

### Medium

| Issue | File | Detail |
|---|---|---|
| `kill -9` (SIGKILL) used instead of SIGTERM | `spark/main.py:68` | `kill -9` doesn't give processes a chance to clean up. `kill -15` (SIGTERM) or just `process.terminate()` is safer. |
| No rate limiting on auth endpoints | `spark/scaffold/app/core/auth.py.tpl` | `/register`, `/token`, `/token/refresh` have no brute-force protection. Consider adding rate limiting via Redis (e.g., `slowapi`). |
| No input size validation on `name` parameter | `spark/utils/add_route.py` (fixed) | Previously no validation on route name — now validates it's a valid Python identifier, but no max length. |
| JWT `sub` is a UUID without audience claim | `spark/scaffold/app/services/auth_service.py.tpl` | No `aud` claim in JWT. If the same secret is used across services, a token from one service could be used in another. |

### Low

| Issue | File | Detail |
|---|---|---|
| No password complexity requirements | `spark/scaffold/app/schemas.py.tpl` | Password field is just `str` — no min length, no complexity validation. |
| SQLAlchemy `echo=False` | `spark/scaffold/app/core/database.py.tpl:13` | Fine for production, but consider making it configurable via env var for debugging. |

---

## Error Handling

### Spark CLI (Good coverage after fixes)

| Command | Before | After |
|---|---|---|
| `create` | Already had structured catches for `ScaffoldError`, `DependencyError`, `AlembicError`, `Exception` | Same (good) |
| `add-route` | No error handling at all — raw exceptions to user | Catches `AddRouteError`, logs exception, shows red error, exits with code 1 |
| `dev` | `FileNotFoundError`, `KeyboardInterrupt`, `OSError` | Same (good for this scope) |
| `_free_port` | No error handling — raw `FileNotFoundError` if `lsof` missing | Catches `FileNotFoundError` (lsof not installed), `OSError` (permission issues). Warnings instead of crashes |

### `add_route_file` (Fixed)

| Scenario | Before | After |
|---|---|---|
| Empty/invalid name | Crashed with OS error | Raises `InvalidRouteNameError` |
| Duplicate route file | Silently overwrote existing file | Raises error with clear message |
| Missing markers in main.py | Silent no-op — import/include lines silently dropped | Raises `MissingMarkerError` with guidance |
| File write failure | Unhandled OSError | Raised as `AddRouteError` with context |

### Scaffold Templates (Needs work)

| Issue | File | Detail |
|---|---|---|
| Redis connection failure | `app/core/auth.py.tpl:28` | `aioredis.from_url()` raises if Redis is down. No try/except, no fallback, no graceful degradation. App crashes on startup if Redis is unavailable. |
| DB connection failure | `app/core/database.py.tpl` | `create_async_engine()` and `init_db()` have no error handling. Migration and server startup crashes without useful error messages. |
| Auth endpoint failures | `app/core/auth.py.tpl` | Routes don't catch exceptions from Redis or DB calls — 500 errors returned without structured logging. |
| Decode error ambiguity | `app/services/auth_service.py.tpl:75` | `decode_token` returns `None` for expired, malformed, invalid-sig, or missing-claim tokens. Callers can't distinguish or respond differently. |

### Recommended approach for scaffold templates

The scaffold templates should use a **middleware + structured exception handler** pattern:

```python
# app/core/exceptions.py
class AppError(Exception):
    status_code: int
    detail: str
    log_level: str = "error"

class DatabaseError(AppError):
    status_code = 500
    detail = "Database operation failed"

class AuthError(AppError):
    status_code = 401
    detail = "Authentication failed"

# app/main.py — generic handler
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    getattr(logger, exc.log_level)(
        "[red]%s[/]: %s", exc.__class__.__name__, rich_escape(exc.detail),
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# app/core/database.py — safe init
async def init_db() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.critical("Database initialization failed: %s", e)
        raise DatabaseError("Database initialization failed") from e
```

---

## Logging

### What's good

- `logging_middleware.py.tpl` has structured per-request logging with method/status colors, duration, and client host
- `rich` handler with markup and tracebacks is well-configured in `logging_config.py.tpl`
- `spark/main.py` uses `logger.exception()` which captures full traceback
- SQLAlchemy and uvicorn access logs are suppressed to avoid noise

### What's missing / could improve

| Area | Detail |
|---|---|
| **Request IDs** | No `request_id` in logs — hard to correlate log lines for a single request across services. Add UUID per request via middleware. |
| **Structured logging** | Rich markup is good for terminal, but consider `python-json-logger` for production — JSON logs are parseable by log aggregators (Datadog, Grafana Loki, etc.). |
| **Redis errors** | Not logged in `auth.py.tpl`. All Redis calls should wrap in try/except with `logger.exception()`. |
| **DB connection errors** | Not logged in `database.py.tpl`. `create_async_engine` failures aren't captured. |
| **Alembic output** | `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL` in `api.py:38` drops migration output. Consider capturing and logging on failure. |
| **Log level for sensitive routes** | Auth endpoints log at WARNING/ERROR but `register` and `login` failures should log at INFO (not WARNING) — repeated failures from the same IP are a signal worth logging at WARNING. |

---

## Architecture & Testability

### Positive

- Clean separation: `spark/main.py` (CLI) → `spark/cli.py` (orchestrator) → `spark/utils/` (implementations)
- Exception hierarchy is well-structured (`ScaffoldError`, `DependencyError`, `AlembicError`)
- Template system via Jinja2 is straightforward
- Test suite uses `tmp_path`, `unittest.mock`, and `pytest.raises` effectively

### Issues

| Issue | Detail |
|---|---|
| **Heavy mocking** | `test_create_api_project.py` mocks `Path.mkdir`, `Path.write_text`, and template rendering — it tests that functions are called but not that the output is correct. Consider a single golden-file integration test that creates a real project in `tmp_path` and checks file structure/contents. |
| **Missing marker test** | No test for the case where `# from app.routers import` marker is missing from `main.py`. |
| **Env var leakage** | `api.py` passes `SECRET_KEY` and `project_name` to all templates, even those that don't use them (like `.gitignore.tpl`). Fine but unnecessary coupling. |
| **`create_api_project` is not idempotent** | Running `create_api_project` twice on the same directory would fail on the second `mkdir` (`.github/workflows` already exists, but `exist_ok=True` on parents handles this — though test dir creation might overwrite files). |
| **No validation after scaffolding** | No check that the scaffolded project can actually be imported (e.g., `uv run python -c "import app.main"`). |
| **Dependency list in source** | `API_DEPS` in `deps.py` is locked to specific packages. No extensibility for users who want different DBs (MySQL, SQLite) or no Redis. |

---

## Specific Bugs Found

| Bug | File | Detail |
|---|---|---|
| **Missing scaffold template** | `spark/utils/api.py` | `".github/workflows/ci.yaml.tpl"` was added to `templates` list but the file didn't exist in scaffold directory. **Fixed.** |
| **Silent wire failure** | `spark/utils/add_route.py` | If `main.py` was missing the `# from app.routers import` or `# --- router marker ---` markers, the `replace()` calls silently did nothing — no import or `include_router` line was added. **Fixed.** |
| **No input validation** | `spark/utils/add_route.py` | Route names like `"my-route"` or `""` would create invalid `.py` filenames. **Fixed.** |

---

## Recommendations Summary

### Immediate (Do now)
1. ~~Add error handling to `add_route` command~~ ✅ Done
2. ~~Add error handling to `_free_port`~~ ✅ Done
3. ~~Add input validation to `add_route_file`~~ ✅ Done
4. ~~Create missing `ci.yaml.tpl` scaffold template~~ ✅ Done
5. Read `CORS_ORIGINS` from env var in `main.py.tpl`
6. Use `os.getenv("SECRET_KEY")` with validation in `auth.py.tpl`
7. Validate DB env vars before constructing URL in `database.py.tpl`

### Short-term (Next sprint)
8. Add Redis connection error handling in `auth.py.tpl`
9. Add graceful DB connection failure handling in `database.py.tpl`
10. Add request ID to middleware for log correlation
11. Add rate limiting to auth endpoints
12. Add password min-length validation to `schemas.py.tpl`
13. Add golden-file integration test for scaffolding output

### Medium-term
14. Switch to structured JSON logging config for production
15. Make dependency list extensible (optional extras in pyproject.toml)
16. Add `aud` claim to JWT tokens
17. Replace `kill -9` with SIGTERM in `_free_port`
18. Consider async-friendly `alembic` template (currently calls `asyncio.run()` which can conflict with running event loop)

---

*Generated for review. Over 50 files examined across source, scaffold templates, and tests.*
