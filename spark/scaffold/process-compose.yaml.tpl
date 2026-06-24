version: "1"

processes:
  web:
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
    availability:
      restart: on_failure

  redis:
    command: redis-server --port ${REDIS_PORT:-6379}
    availability:
      restart: on_failure
