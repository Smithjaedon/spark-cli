import logging
import os
import subprocess

import typer
from rich.console import Console
from rich.text import Text

from spark.cli import spark_create_init
from spark.utils.exceptions import (
    AlembicError,
    DependencyError,
    InvalidOptionError,
    ScaffoldError,
)

logger = logging.getLogger(__name__)
app = typer.Typer()
console = Console()


@app.command("create", help="creates spark project structure")
def create() -> None:
    console.print(Text("Spark", style="cyan"))
    try:
        spark_create_init()
    except InvalidOptionError:
        logger.exception("Invalid project type selected.")
        console.print("[red]Invalid project type selected.[/]")
        raise typer.Exit(code=1)
    except ScaffoldError:
        logger.exception("Scaffolding error occurred.")
        console.print("[red]Scaffolding failed.[/]")
        raise typer.Exit(code=1)
    except DependencyError:
        logger.exception("Dependency installation error occurred.")
        console.print("[red]Dependency installation failed.[/]")
        raise typer.Exit(code=1)
    except AlembicError:
        logger.exception("Alembic setup error occurred.")
        console.print("[red]Alembic setup failed.[/]")
        raise typer.Exit(code=1)
    except Exception:
        logger.exception("An unexpected error occurred.")
        console.print("[red]Project creation failed unexpectedly.[/]")
        raise typer.Exit(code=1)

    console.print(Text("Done.", style="bold green"))


def _free_port(port: int) -> None:
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        for pid in result.stdout.strip().split():
            logger.info("Killing process %s holding port %s", pid, port)
            subprocess.run(["kill", "-9", pid], capture_output=True)


@app.command("dev", help="run process-compose up for the project")
def dev() -> None:
    _free_port(8080)
    _free_port(int(os.environ.get("PORT", "8000")))
    _free_port(int(os.environ.get("REDIS_PORT", "6379")))

    proc: subprocess.Popen[bytes] | None = None
    try:
        proc = subprocess.Popen(["process-compose", "up"])
        proc.wait()
    except FileNotFoundError:
        logger.exception("process-compose not found in PATH.")
        console.print(
            "[red]process-compose not found.[/]\n"
            "Please install process-compose and ensure it's in your PATH."
        )
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    except OSError as e:
        logger.exception("Error running process-compose.")
        console.print(f"[red]Error running process-compose:[/] {e}")
        raise typer.Exit(code=1)
