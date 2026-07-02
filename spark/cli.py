import logging
import os

from rich.console import Console

from spark.utils.api import create_api_project, initialize_dependencies, setup_alembic

logger = logging.getLogger(__name__)
console = Console()


def spark_create_init() -> None:
    output_dir = os.getcwd()
    with console.status("Installing dependencies..."):
        initialize_dependencies(output_dir)
    with console.status("Scaffolding project files..."):
        create_api_project(output_dir)
    with console.status("Setting up Alembic..."):
        setup_alembic(output_dir)
