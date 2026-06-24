import subprocess

import typer
from rich.console import Console
from rich.text import Text

from spark.cli import spark_create_init

app = typer.Typer()
console = Console()


@app.command("create", help="creates spark project structure")
def create() -> None:
    console.print(Text("Spark", style="cyan"))
    try:
        spark_create_init()
    except Exception:
        pass
    console.print(Text("Done.", style="bold green"))


@app.command("dev", help="run process-compose up for the project")
def dev() -> None:
    try:
        subprocess.run(["process-compose", "up"], check=True)
    except FileNotFoundError:
        console.print(
            "[red]process-compose not found.[/]\n"
            "Please install process-compose and ensure it's in your PATH."
        )
        raise typer.Exit(code=1)
    except OSError as e:
        console.print(f"[red]Error running process-compose:[/] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/] {e}")
        raise typer.Exit(code=1)
