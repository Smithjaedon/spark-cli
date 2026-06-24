import logging
import time

from fastapi import Request

logger = logging.getLogger("api.access")


async def logging_middleware(request: Request, call_next):
    url = request.url.path
    if request.query_params:
        url = f"{url}?{request.query_params}"

    client_host = request.client.host if request.client else "unknown"
    start = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start
    status = response.status_code
    method = request.method

    logger.info(
        "%s %s [%s] %s — %dms",
        method,
        url,
        client_host,
        status,
        int(elapsed * 1000),
    )
    return response
