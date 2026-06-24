import os
import secrets

from spark.utils.template_config import env


def create_api_project() -> None:
    templates = [
        "app/core/auth.py.tpl",
        "app/core/database.py.tpl",
        "app/core/exceptions.py.tpl",
        "app/core/logging_config.py.tpl",
        "app/models.py.tpl",
        "app/schemas.py.tpl",
        "app/main.py.tpl",
        "app/services/auth_service.py.tpl",
        "app/services/user_service.py.tpl",
        ".env.tpl",
    ]

    base = os.path.join(os.getcwd(), "main.py")
    if not os.path.exists(base):
        raise FileNotFoundError(
            f"Cannot create API project: {base} does not exist. Please run 'spark create' first."
        )
    os.remove(base)

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
