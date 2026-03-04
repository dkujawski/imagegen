"""Command-line entrypoint for imagegen."""

import typer

app = typer.Typer(help="Generate images from the command line.")


@app.callback()
def main() -> None:
    """Image generation command-line interface."""
