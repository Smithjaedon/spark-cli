import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

ROUTE_TEMPLATE = """from fastapi import APIRouter

route = APIRouter()
"""

IMPORT_MARKER = "# from app.routers import"
INCLUDE_MARKER = "# --- router marker ---"


class AddRouteError(Exception):
    pass


class InvalidRouteNameError(AddRouteError):
    pass


class MissingMarkerError(AddRouteError):
    pass


def _validate_name(name: str) -> None:
    if not name or not name.strip():
        raise InvalidRouteNameError("Route name cannot be empty")
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise InvalidRouteNameError(
            f"Invalid route name: {name!r}. Must be a valid Python identifier."
        )


def add_route_file(project_dir: str, name: str) -> Path:
    _validate_name(name)

    routes_dir = Path(project_dir) / "app" / "routes"
    route_file = routes_dir / f"{name}.py"

    if route_file.exists():
        raise AddRouteError(f"Route file already exists: {route_file}")

    try:
        routes_dir.mkdir(parents=True, exist_ok=True)
        route_file.write_text(ROUTE_TEMPLATE.lstrip())
    except OSError as e:
        raise AddRouteError(f"Failed to create route file at {route_file}: {e}") from e

    main_py = Path(project_dir) / "app" / "main.py"
    if main_py.exists():
        try:
            content = main_py.read_text()
        except OSError as e:
            raise AddRouteError(f"Failed to update {main_py}: {e}") from e

        import_line = f"from app.routes.{name} import route as {name}"
        include_line = f"app.include_router({name})"

        if import_line not in content:
            if IMPORT_MARKER not in content:
                raise MissingMarkerError(
                    f"Marker {IMPORT_MARKER!r} not found in {main_py}. "
                    "Cannot auto-wire import statement."
                )
            content = content.replace(
                IMPORT_MARKER,
                f"{IMPORT_MARKER}\n{import_line}",
                1,
            )

        if include_line not in content:
            if INCLUDE_MARKER not in content:
                raise MissingMarkerError(
                    f"Marker {INCLUDE_MARKER!r} not found in {main_py}. "
                    "Cannot auto-wire include_router statement."
                )
            content = content.replace(
                INCLUDE_MARKER,
                f"{include_line}\n{INCLUDE_MARKER}",
                1,
            )

        try:
            main_py.write_text(content)
        except OSError as e:
            raise AddRouteError(f"Failed to update {main_py}: {e}") from e

    return route_file
