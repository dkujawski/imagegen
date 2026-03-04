# imagegen

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
