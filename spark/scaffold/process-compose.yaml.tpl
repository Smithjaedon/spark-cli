version: "1"

processes:
  web:
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
    shutdown:
      signal: SIGINT
      timeout: 10s
    availability:
      restart: on_failure

  redis:
    command: redis-server --port ${REDIS_PORT:-6379}
    shutdown:
      signal: SIGTERM
      timeout: 10s
    availability:
      restart: on_failure
