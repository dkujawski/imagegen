from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .filter_manifest import FilterDefinition, ParameterDefinition, load_manifest


def _arg_type_for(param: ParameterDefinition):
    if param.type == "int":
        return int
    if param.type == "float":
        return float
    if param.type == "bool":
        return lambda v: v.lower() in {"1", "true", "yes", "on"}
    return str


def _add_manifest_parameter(parser: argparse.ArgumentParser, param: ParameterDefinition) -> None:
    arg_name = f"--{param.name.replace('_', '-')}"
    kwargs: dict[str, object] = {"default": param.default, "help": f"{param.type} parameter"}

    if param.type == "enum":
        kwargs["choices"] = param.enum
        kwargs["type"] = str
    else:
        kwargs["type"] = _arg_type_for(param)

    parser.add_argument(arg_name, required=param.default is None, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    manifest = load_manifest()
    parser = argparse.ArgumentParser(prog="imagegen")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list-filters", help="List filters from the manifest")
    list_parser.add_argument("--category", help="Only show filters in this category")
    list_parser.add_argument("--tag", action="append", default=[], help="Only show filters with all tags")
    list_parser.set_defaults(_manifest=manifest)

    inspect_parser = sub.add_parser("inspect-filter", help="Inspect one filter schema")
    inspect_parser.add_argument("filter_id")
    inspect_parser.add_argument("--json", action="store_true", help="Dump as JSON")
    inspect_parser.set_defaults(_manifest=manifest)

    run_parser = sub.add_parser("run-filter", help="Execute a filter script using manifest-defined parameters")
    run_parser.add_argument("filter_id")
    run_parser.add_argument("--dry-run", action="store_true", help="Only print script command")
    run_parser.set_defaults(_manifest=manifest)

    return parser


def cmd_list_filters(args: argparse.Namespace) -> int:
    filters = args._manifest.filters
    if args.category:
        filters = [f for f in filters if f.category == args.category]
    if args.tag:
        required_tags = set(args.tag)
        filters = [f for f in filters if required_tags.issubset(set(f.tags))]

    for f in filters:
        print(f"{f.id:28} {f.name:30} category={f.category} tags={','.join(f.tags)}")
    return 0


def _filter_to_jsonable(filter_def: FilterDefinition) -> dict:
    return {
        "id": filter_def.id,
        "name": filter_def.name,
        "script_path": filter_def.script_path,
        "category": filter_def.category,
        "tags": filter_def.tags,
        "parameters": [p.__dict__ for p in filter_def.parameters],
        "output": filter_def.output,
    }


def cmd_inspect_filter(args: argparse.Namespace) -> int:
    f = args._manifest.by_id(args.filter_id)
    if not f:
        raise SystemExit(f"unknown filter: {args.filter_id}")

    payload = _filter_to_jsonable(f)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{f.id}: {f.name}")
        print(f"  script: {f.script_path}")
        print(f"  category: {f.category}")
        print(f"  tags: {', '.join(f.tags)}")
        print("  parameters:")
        for p in f.parameters:
            bits = [f"type={p.type}"]
            if p.default is not None:
                bits.append(f"default={p.default}")
            if p.min is not None:
                bits.append(f"min={p.min}")
            if p.max is not None:
                bits.append(f"max={p.max}")
            if p.step is not None:
                bits.append(f"step={p.step}")
            if p.enum:
                bits.append(f"enum={','.join(p.enum)}")
            print(f"    - {p.name}: {' '.join(bits)}")
        print(f"  output: {json.dumps(f.output)}")
    return 0


def _parse_filter_args(filter_def: FilterDefinition, extras: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=f"imagegen run-filter {filter_def.id}")
    for param in filter_def.parameters:
        _add_manifest_parameter(parser, param)
    return parser.parse_args(extras)


def cmd_run_filter(args: argparse.Namespace, extras: list[str]) -> int:
    f = args._manifest.by_id(args.filter_id)
    if not f:
        raise SystemExit(f"unknown filter: {args.filter_id}")

    parsed = _parse_filter_args(f, extras)
    values = {p.name: getattr(parsed, p.name) for p in f.parameters}
    script = Path(__file__).resolve().parents[1] / f.script_path

    cmd = [str(script), str(values["size"]), str(values["output_dir"]), str(values["file_name"])]
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    subprocess.run(cmd, check=True)
    return 0


def main() -> int:
    parser = build_parser()
    args, extras = parser.parse_known_args()

    if args.command == "list-filters":
        return cmd_list_filters(args)
    if args.command == "inspect-filter":
        return cmd_inspect_filter(args)
    if args.command == "run-filter":
        return cmd_run_filter(args, extras)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
