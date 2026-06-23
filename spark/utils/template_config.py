from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent.parent / "scaffold"),
    autoescape=select_autoescape(),
)
