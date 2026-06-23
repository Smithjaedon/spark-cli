from rich.prompt import Prompt

from spark.utils.api import create_api_project
from spark.utils.exceptions import InvalidOptionError


class ProjectType:
    BASIC = "basic"
    API = "api"


def spark_create_init() -> None:
    project_type = Prompt.ask("What type of project are you creating?")
    if project_type == ProjectType.BASIC:
        pass
    elif project_type == ProjectType.API:
        create_api_project()
    else:
        raise InvalidOptionError(
            "Invalid project type: Please choose 'basic' or 'api'."
        )
