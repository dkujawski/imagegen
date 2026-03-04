"""Command-line entrypoint for imagegen."""

from __future__ import annotations

import typer

app = typer.Typer(help="Generate images from the command line.")


@app.command("gui")
def gui() -> None:
    """Run the local-first desktop GUI."""
    from .gui import run_gui

    raise typer.Exit(code=run_gui())


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Default command."""
    if ctx.invoked_subcommand is None:
        typer.echo("Use 'imagegen gui' to launch the desktop UI.")
