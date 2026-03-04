# imagegen

Generate images from the command line for testing and experimentation.

## Environment and packaging (uv + venv)

This project is packaged as a Python application (`pyproject.toml`) and works best with `uv`.

```bash
uv venv .venv
source .venv/bin/activate
uv sync
```

Install the package in editable mode with optional GUI dependencies:

```bash
uv sync --extra gui
```

Run commands inside the project environment without activating:

```bash
uv run imagegen --help
```

## CLI

This repository includes a Python CLI package in `src/imagegen_cli`.

```bash
uv run imagegen list-filters
uv run imagegen inspect-filter fractal_swirl
uv run imagegen run-filter fractal_swirl --size 256 --output-dir ./out --file-name sample
```

`run-filter` arguments are generated from the manifest schema so the same parameter metadata can be reused by a GUI.

## Filter manifest

`filters.json` is the single source of truth for generator metadata and parameter schemas.
Each entry provides:

- human-readable name, script path, category, and tags
- parameter definitions (`name`, `type`, `min`/`max`, `default`, `step`, enum choices)
- output behavior and preview-safe limits for UIs

## Local-first GUI (PySide6)

A desktop GUI is available with a manifest-driven control panel and asynchronous render runner:

```bash
uv run imagegen gui
```

Implemented flow:

1. Select a filter from `filters.json`
2. Controls are generated dynamically from each parameter schema
3. Click **Generate** to run an async job thread that executes ImageMagick scripts
4. A preview stage renders first at preview-safe size, then full render at requested size
5. Progress and logs stream into the UI in real time via a thread-safe event queue
6. **Cancel** stops the process group and cleans temporary preview files
