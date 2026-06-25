import os
import secrets
import subprocess

from spark.utils.deps import API_DEPS
from spark.utils.template_config import env


def create_api_project() -> None:
    templates = [
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

    base = os.path.join(os.getcwd(), "main.py")
    if os.path.exists(base):
        os.remove(base)

    gitignore = os.path.join(os.getcwd(), ".gitignore")
    if os.path.exists(gitignore):
        os.remove(gitignore)

    secret_key = secrets.token_urlsafe(32)

    for tpl_path in templates:
        out_path = os.path.join(os.getcwd(), tpl_path.removesuffix(".tpl"))
        parent = os.path.dirname(out_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        template = env.get_template(tpl_path)
        rendered = template.render(SECRET_KEY=secret_key)
        with open(out_path, "w") as f:
            f.write(rendered)

    tests_root = os.path.join(os.getcwd(), "tests")
    os.makedirs(os.path.join(tests_root, "integrations"), exist_ok=True)
    os.makedirs(os.path.join(tests_root, "unit"), exist_ok=True)


def initalize_dependencies() -> None:
    output_dir = os.getcwd()
    subprocess.run(["uv", "init"], cwd=output_dir, check=True)
    subprocess.run(["uv", "add"] + API_DEPS, cwd=output_dir, check=True)


def setup_alembic() -> None:
    output_dir = os.getcwd()
    subprocess.run(["alembic", "init", "alembic"], cwd=output_dir, check=True)
