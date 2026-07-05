import pytest
from pathlib import Path

from spark.utils.add_route import AddRouteError, add_route_file

MAIN_TPL = """# from app.routers import

app.include_router(auth)
# --- router marker ---
"""


class TestAddRouteFile:
    def test_creates_route_file_and_wires_main(self, tmp_path) -> None:
        project_dir = tmp_path / "my_project"
        app_dir = project_dir / "app"
        app_dir.mkdir(parents=True)
        main_py = app_dir / "main.py"
        main_py.write_text(MAIN_TPL)

        result = add_route_file(str(project_dir), "items")

        expected_file = project_dir / "app" / "routes" / "items.py"
        assert result == expected_file
        assert (
            expected_file.read_text()
            == "from fastapi import APIRouter\n\nroute = APIRouter()\n"
        )
        assert "from app.routes.items import route as items" in main_py.read_text()
        assert "app.include_router(items)" in main_py.read_text()

    def test_skips_wiring_if_main_py_missing(self, tmp_path) -> None:
        project_dir = tmp_path / "my_project"
        (project_dir / "app").mkdir(parents=True)

        add_route_file(str(project_dir), "users")

        assert (project_dir / "app" / "routes" / "users.py").exists()

    def test_raises_on_duplicate_route(self, tmp_path) -> None:
        project_dir = tmp_path / "my_project"
        app_dir = project_dir / "app"
        app_dir.mkdir(parents=True)
        main_py = app_dir / "main.py"
        main_py.write_text(MAIN_TPL)

        add_route_file(str(project_dir), "items")
        with pytest.raises(AddRouteError, match="Route file already exists"):
            add_route_file(str(project_dir), "items")

    def test_rejects_invalid_route_names(self, tmp_path) -> None:
        project_dir = tmp_path / "my_project"
        (project_dir / "app").mkdir(parents=True)

        with pytest.raises(AddRouteError, match="Route name cannot be empty"):
            add_route_file(str(project_dir), "")

        with pytest.raises(AddRouteError, match="Invalid route name"):
            add_route_file(str(project_dir), "my-route")

        with pytest.raises(AddRouteError, match="Invalid route name"):
            add_route_file(str(project_dir), "123abc")

    def test_display_path_uses_project_folder_name(self, tmp_path) -> None:
        project_dir = tmp_path / "my_project"
        (project_dir / "app").mkdir(parents=True)

        route_path = add_route_file(str(project_dir), "users")

        project_root = project_dir
        display_path = Path(project_root.name) / route_path.relative_to(project_root)
        expected = Path("my_project") / "app" / "routes" / "users.py"
        assert display_path == expected
        assert str(display_path) == "my_project/app/routes/users.py"
