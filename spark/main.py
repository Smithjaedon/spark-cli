import logging
import os
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

from spark.cli import spark_create_init
from spark.utils.add_route import AddRouteError, add_route_file
from spark.utils.exceptions import (
    AlembicError,
    DependencyError,
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


@app.command("add-route", help="adds a route file to app/routes/")
def add_route(name: str) -> None:
    try:
        path = add_route_file(os.getcwd(), name)
    except AddRouteError:
        logger.exception("Failed to add route.")
        console.print("[red]Failed to add route.[/]")
        raise typer.Exit(code=1)

    project_root = Path(os.getcwd())
    display_path = Path(project_root.name) / path.relative_to(project_root)
    console.print(f"[green]Created {display_path}[/]")


def _free_port(port: int) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        logger.warning("lsof not found; cannot check port %s", port)
        return
    except OSError as e:
        logger.warning("Failed to check port %s: %s", port, e)
        return

    if result.stdout.strip():
        for pid in result.stdout.strip().split():
            logger.info("Killing process %s holding port %s", pid, port)
            try:
                subprocess.run(["kill", "-9", pid], capture_output=True, check=True)
            except (FileNotFoundError, OSError) as e:
                logger.warning("Failed to kill process %s on port %s: %s", pid, port, e)


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
