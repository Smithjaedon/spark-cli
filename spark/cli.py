import logging
import os

import questionary
from rich.console import Console

from spark.utils.api import create_api_project, initialize_dependencies, setup_alembic
from spark.utils.exceptions import InvalidOptionError

logger = logging.getLogger(__name__)
console = Console()


class ProjectType:
    BASIC = "basic"
    API = "api"


def spark_create_init() -> None:
    project_type = questionary.select(
        "What type of project are you creating?",
        choices=[
            questionary.Choice(title="Basic", value=ProjectType.BASIC),
            questionary.Choice(title="API (FastAPI)", value=ProjectType.API),
        ],
    ).ask()
    if project_type == ProjectType.BASIC:
        pass
    elif project_type == ProjectType.API:
        output_dir = os.getcwd()
        with console.status("Scaffolding project files..."):
            create_api_project(output_dir)
        with console.status("Installing dependencies..."):
            initialize_dependencies(output_dir)
        with console.status("Setting up Alembic..."):
            setup_alembic(output_dir)
    else:
        raise InvalidOptionError(
            "Invalid project type: Please choose 'basic' or 'api'."
        )
