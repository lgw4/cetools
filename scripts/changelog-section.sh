#!/usr/bin/env sh
# Extract one version's section body from a changelog. See
# specs/005-release-publishing/contracts/release-scripts.md for the contract.
#
# Usage: changelog-section.sh <version> <changelog-path>
set -eu

if [ $# -ne 2 ]; then
    echo "usage: changelog-section.sh <version> <changelog-path>" >&2
    exit 2
fi

version="$1"
changelog="$2"

if [ ! -f "$changelog" ]; then
    echo "usage: changelog-section.sh <version> <changelog-path>: $changelog not found" >&2
    exit 2
fi

escaped_version=$(printf '%s' "$version" | sed 's/[.[\*^$]/\\&/g')

if ! awk -v pattern="^## ${escaped_version}([[:space:]]|\$)" '
BEGIN { found = 0; in_section = 0; n = 0 }
{
    if (in_section && $0 ~ /^## /) { in_section = 0 }
    if ($0 ~ pattern) { found = 1; in_section = 1; next }
    if (in_section) { n++; lines[n] = $0 }
}
END {
    if (!found) exit 1
    start = 1
    end = n
    while (start <= end && lines[start] ~ /^[[:space:]]*$/) start++
    while (end >= start && lines[end] ~ /^[[:space:]]*$/) end--
    for (i = start; i <= end; i++) print lines[i]
}
' "$changelog"; then
    echo "no changelog section for version $version in $changelog" >&2
    exit 1
fi
