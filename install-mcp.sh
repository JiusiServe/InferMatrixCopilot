#!/usr/bin/env sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
installer="$project_root/scripts/install_mcp.py"

for python_command in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$python_command" >/dev/null 2>&1 &&
        "$python_command" -c \
            'import sys; raise SystemExit(sys.version_info < (3, 11))'
    then
        exec "$python_command" "$installer" "$@"
    fi
done

echo "Python 3.11 or newer is required." >&2
exit 1
