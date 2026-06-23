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
