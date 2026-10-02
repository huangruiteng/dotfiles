#!/bin/sh
# Preview by default. No package installation, credentials, or submodule recursion.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/tools/install.py" "$@"
