from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import click


@dataclass(frozen=True)
class FilterScript:
    name: str
    path: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scripts_dir() -> Path:
    return _repo_root() / "ImageMagick" / "scripts"


def _filter_scripts() -> list[FilterScript]:
    scripts = []
    for script in sorted(_scripts_dir().glob("*.bash")):
        scripts.append(FilterScript(name=script.stem, path=script.resolve()))
    return scripts


def _find_filter(filter_name: str) -> Optional[FilterScript]:
    for script in _filter_scripts():
        if script.name == filter_name:
            return script
    return None


def _validate_positive_int(name: str, value: int) -> int:
    if value <= 0:
        raise click.BadParameter(f"{name} must be a positive integer")
    return value


def _validate_script_path(script_path: Path) -> Path:
    if not script_path.exists():
        raise click.BadParameter(f"Script path does not exist: {script_path}")
    if not script_path.is_file():
        raise click.BadParameter(f"Script path is not a file: {script_path}")
    if not os.access(script_path, os.X_OK):
        raise click.BadParameter(f"Script is not executable: {script_path}")
    return script_path


def _validate_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        raise click.BadParameter(f"Output path is not a directory: {output_dir}")
    if not os.access(output_dir, os.W_OK):
        raise click.BadParameter(f"Output directory is not writable: {output_dir}")
    return output_dir


def _run_commands(commands: Iterable[list[str]], dry_run: bool) -> int:
    for command in commands:
        pretty_command = " ".join(command)
        click.echo(pretty_command)
        if dry_run:
            continue

        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            click.echo(
                f"Generation command failed with exit code {completed.returncode}: {pretty_command}",
                err=True,
            )
            return completed.returncode

    return 0


def _command_set_for_script(script_path: Path, size: int, count: int, output_dir: Path) -> list[list[str]]:
    script_name = script_path.stem
    out_prefix = output_dir / f"{script_name}_{size}_{count}"
    width = len(str(count))
    commands: list[list[str]] = []
    for i in range(1, count + 1):
        sequence = f"{i:0{width}d}"
        commands.append([str(script_path), str(size), str(out_prefix), sequence])
    return commands


@click.group(help="Generate images by running ImageMagick script filters.")
def app() -> None:
    pass


@app.command("list-filters")
def list_filters() -> None:
    """List available filter scripts."""
    scripts = _filter_scripts()
    if not scripts:
        click.echo("No filters found.")
        raise SystemExit(1)

    for script in scripts:
        click.echo(script.name)


@app.command("inspect-filter")
@click.argument("filter_name")
def inspect_filter(filter_name: str) -> None:
    """Show details about a filter script."""
    script = _find_filter(filter_name)
    if script is None:
        click.echo(f"Unknown filter '{filter_name}'. Use list-filters to see options.", err=True)
        raise SystemExit(2)

    click.echo(f"name: {script.name}")
    click.echo(f"path: {script.path}")


@app.command("run-script")
@click.option("--size", required=True, type=int, help="Square image size (px).")
@click.option("--count", required=True, type=int, help="How many images to generate.")
@click.option("--output-dir", required=True, type=click.Path(path_type=Path), help="Output directory.")
@click.option("--filter", "filter_name", type=str, default=None, help="Filter name from list-filters.")
@click.option("--script-path", type=click.Path(path_type=Path), default=None, help="Path to a script file.")
@click.option("--dry-run", is_flag=True, help="Print commands without executing.")
def run_script(
    size: int,
    count: int,
    output_dir: Path,
    filter_name: Optional[str],
    script_path: Optional[Path],
    dry_run: bool,
) -> None:
    """Run one filter script to generate a set of images."""
    size = _validate_positive_int("size", size)
    count = _validate_positive_int("count", count)
    output_dir = _validate_output_dir(output_dir)

    if bool(filter_name) == bool(script_path):
        raise click.BadParameter("Provide exactly one of --filter or --script-path")

    if filter_name:
        script = _find_filter(filter_name)
        if script is None:
            click.echo(f"Unknown filter '{filter_name}'. Use list-filters to see options.", err=True)
            raise SystemExit(2)
        resolved_script = script.path
    else:
        assert script_path is not None
        resolved_script = _validate_script_path(script_path.resolve())

    commands = _command_set_for_script(
        script_path=resolved_script,
        size=size,
        count=count,
        output_dir=output_dir.resolve(),
    )
    raise SystemExit(_run_commands(commands, dry_run=dry_run))


@app.command("run-all")
@click.option("--size", required=True, type=int, help="Square image size (px).")
@click.option("--count", required=True, type=int, help="How many images to generate per script.")
@click.option("--output-dir", required=True, type=click.Path(path_type=Path), help="Output directory.")
@click.option("--dry-run", is_flag=True, help="Print commands without executing.")
def run_all(size: int, count: int, output_dir: Path, dry_run: bool) -> None:
    """Run all discovered filter scripts."""
    size = _validate_positive_int("size", size)
    count = _validate_positive_int("count", count)
    output_dir = _validate_output_dir(output_dir)

    scripts = _filter_scripts()
    if not scripts:
        click.echo("No filters found in ImageMagick/scripts.", err=True)
        raise SystemExit(1)

    commands: list[list[str]] = []
    for script in scripts:
        commands.extend(
            _command_set_for_script(
                script_path=script.path,
                size=size,
                count=count,
                output_dir=output_dir.resolve(),
            )
        )

    raise SystemExit(_run_commands(commands, dry_run=dry_run))


def main() -> None:
    try:
        app(prog_name="imagegen")
    except click.BadParameter as exc:
        click.echo(f"Invalid input: {exc}", err=True)
        raise SystemExit(2) from exc
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
