import logging
import secrets
import subprocess
from pathlib import Path

from spark.utils.deps import API_DEPS
from spark.utils.exceptions import AlembicError, DependencyError
from spark.utils.template_config import env

logger = logging.getLogger(__name__)


def create_api_project(output_dir: str) -> None:
    templates = [
        "README.md.tpl",
        "app/core/auth.py.tpl",
        "app/core/database.py.tpl",
        "app/core/exceptions.py.tpl",
        "app/core/logging_config.py.tpl",
        "app/middleware/logging_middleware.py.tpl",
        "app/models.py.tpl",
        "app/schemas.py.tpl",
        "app/main.py.tpl",
        "app/services/auth_service.py.tpl",
        "app/services/user_service.py.tpl",
        ".env.tpl",
        ".gitignore.tpl",
        "process-compose.yaml.tpl",
    ]

    secret_key = secrets.token_urlsafe(32)
    out_dir = Path(output_dir)

    parents: set[Path] = set()
    paths: list[Path] = []
    for tpl_path in templates:
        out = out_dir / tpl_path.removesuffix(".tpl")
        paths.append(out)
        parent = out.parent
        if parent != out_dir:
            parents.add(parent)

    for parent in parents:
        parent.mkdir(parents=True, exist_ok=True)

    for out, tpl_path in zip(paths, templates):
        template = env.get_template(tpl_path)
        rendered = template.render(
            SECRET_KEY=secret_key,
            project_name=out_dir.name,
        )
        out.write_text(rendered)

    tests_root = out_dir / "tests"
    (tests_root / "integrations").mkdir(parents=True, exist_ok=True)
    (tests_root / "unit").mkdir(parents=True, exist_ok=True)


def initialize_dependencies(output_dir: str) -> None:
    try:
        subprocess.run(
            ["uv", "init", "--no-readme"],
            cwd=output_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        Path(output_dir, "main.py").unlink(missing_ok=True)
        subprocess.run(
            ["uv", "add", *API_DEPS],
            cwd=output_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, OSError):
        logger.exception("dependency installation failed")
        raise DependencyError("Failed to install project dependencies")


def setup_alembic(output_dir: str) -> None:
    try:
        subprocess.run(
            ["alembic", "init", "alembic"],
            cwd=output_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        tpl = env.get_template("alembic/env.py.tpl")
        rendered = tpl.render()
        dest = Path(output_dir, "alembic", "env.py")
        dest.write_text(rendered)
    except (subprocess.CalledProcessError, OSError):
        logger.exception("alembic init failed")
        raise AlembicError("Failed to initialize Alembic migrations")
