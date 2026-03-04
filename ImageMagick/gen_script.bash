#!/bin/bash
set -euo pipefail

if [ $# -lt 4 ]; then
    echo "missing params"
    echo "${0} size count outputdir script"
    exit 2
fi

size=${1}
count=${2}
output_dir=${3}
script_path=${4}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[DEPRECATED] gen_script.bash is a compatibility shim. Please use imagegen run-script." >&2
PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
python3 -m imagegen_cli run-script \
    --size "${size}" \
    --count "${count}" \
    --output-dir "${output_dir}" \
    --script-path "${script_path}"
