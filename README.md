# imagegen

generate images from the commandline for testing and stuff.

## CLI

This repository now includes a Python CLI package at `src/imagegen_cli`.

From the repository root, run:

```bash
PYTHONPATH=src python3 -m imagegen_cli --help
generate images from the commandline for testing and stuff

## Filter manifest

`filters.json` is the single source of truth for generator metadata and parameter schemas.
Each manifest entry provides:

- human-readable name, script path, category, and tags
- parameter definitions (`name`, `type`, `min`/`max`, `default`, `step`, enum choices)
- output behavior + preview-safe limits for UIs

## CLI

Run the Python CLI with:

```bash
python -m imagegen_cli list-filters
python -m imagegen_cli inspect-filter fractal_swirl
python -m imagegen_cli inspect-filter fractal_swirl --json
python -m imagegen_cli run-filter fractal_swirl --size 256 --output-dir ./out --file-name sample
```

`run-filter` arguments are generated from the manifest schema, so CLI control definitions can be reused by future GUI rendering.
## Install

```bash
pip install .
```

## Run

```bash
imagegen --help
```


## Local-first GUI (PySide6)

A desktop GUI is available with a manifest-driven control panel and async render runner:

```bash
pip install .[gui]
imagegen gui
```

Implemented end-to-end flow:

1. Select a filter from `filters.json`
2. UI controls are generated dynamically from each filter parameter schema
3. Click **Generate** to run an async job thread that executes ImageMagick scripts
4. A preview stage renders first at preview-safe size, then full render at requested size
5. Progress + logs stream into the UI in realtime via a thread-safe event queue
6. **Cancel** stops the process group and cleans temporary preview files
