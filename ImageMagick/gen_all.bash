#!/bin/bash
set -euo pipefail

if [ $# -lt 3 ]; then
    echo "missing params"
    echo "${0} size count outputdir"
    exit 2
fi

size=${1}
count=${2}
output_dir=${3}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[DEPRECATED] gen_all.bash is a compatibility shim. Please use imagegen run-all." >&2
PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
python3 -m imagegen_cli run-all \
    --size "${size}" \
    --count "${count}" \
    --output-dir "${output_dir}"
