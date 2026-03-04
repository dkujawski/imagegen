Generate a bunch of images for testing.
Requires a recent install of ImageMagick: www.imagemagick.org


## Environment (uv)

From the repository root:

```bash
uv venv .venv
source .venv/bin/activate
uv sync
```

Then run CLI commands using `uv run`:

```bash
uv run imagegen run-all --size 256 --count 1 --output-dir ./out
```

## Modern CLI

A new Python CLI is available via `imagegen` with subcommands:

- `run-script`
- `run-all`
- `list-filters`
- `inspect-filter`

Example usage:

```bash
python3 -m imagegen_cli list-filters
python3 -m imagegen_cli run-all --size 256 --count 1 --output-dir ./out
python3 -m imagegen_cli run-script --size 512 --count 30 --output-dir ./out --filter fractal_swirl
python3 -m imagegen_cli run-script --size 512 --count 30 --output-dir ./out --script-path ./ImageMagick/scripts/fractal_swirl.bash
```

Use `--dry-run` with `run-script` or `run-all` to print the generated ImageMagick commands without executing them.

## Compatibility shims

`gen_script.bash` and `gen_all.bash` are now compatibility shims that forward to the Python CLI and print a deprecation notice.

Legacy examples still work:

```bash
./gen_all.bash 256 1 ./out
./gen_script.bash 512 30 ./out ./scripts/fractal_swirl.bash
```
