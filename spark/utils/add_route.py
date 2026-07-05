from pathlib import Path

ROUTE_TEMPLATE = """from fastapi import APIRouter

route = APIRouter()
"""


def add_route_file(project_dir: str, name: str) -> Path:
    routes_dir = Path(project_dir) / "app" / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    route_file = routes_dir / f"{name}.py"
    route_file.write_text(ROUTE_TEMPLATE.lstrip())

    main_py = Path(project_dir) / "app" / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        import_line = f"from app.routes.{name} import route as {name}"
        include_line = f"app.include_router({name})"

        if import_line not in content:
            content = content.replace(
                "# from app.routers import",
                f"# from app.routers import\n{import_line}",
            )

        if include_line not in content:
            content = content.replace(
                "# --- router marker ---",
                f"{include_line}\n# --- router marker ---",
            )

        main_py.write_text(content)

    return route_file
