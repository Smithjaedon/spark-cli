import logging
import os
import secrets
import subprocess

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
    project_name = os.path.basename(os.path.abspath(output_dir))

    for tpl_path in templates:
        out_path = os.path.join(output_dir, tpl_path.removesuffix(".tpl"))
        parent = os.path.dirname(out_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        template = env.get_template(tpl_path)
        rendered = template.render(SECRET_KEY=secret_key, project_name=project_name)
        with open(out_path, "w") as f:
            f.write(rendered)

    tests_root = os.path.join(output_dir, "tests")
    os.makedirs(os.path.join(tests_root, "integrations"), exist_ok=True)
    os.makedirs(os.path.join(tests_root, "unit"), exist_ok=True)


def initialize_dependencies(output_dir: str) -> None:
    try:
        subprocess.run(
            ["uv", "init"],
            cwd=output_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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
        dest = os.path.join(output_dir, "alembic", "env.py")
        with open(dest, "w") as f:
            f.write(rendered)
    except (subprocess.CalledProcessError, OSError):
        logger.exception("alembic init failed")
        raise AlembicError("Failed to initialize Alembic migrations")
