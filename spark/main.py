import typer
from rich.console import Console
from rich.text import Text

app = typer.Typer()
console = Console()


@app.command("create", help="creates spark project structure")
def create() -> None:
    console.print(Text("Spark", style="cyan"))
    try:
        pass
    except Exception:
        pass
    console.print(Text("Done.", style="bold green"))
