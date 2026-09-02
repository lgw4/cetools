#!/usr/bin/env sh
# Refuse a cetools release that would ship something wrong. See
# specs/005-release-publishing/contracts/release-scripts.md for the contract.
#
# Usage: release-preflight.sh <tag> <pyproject-path> <changelog-path>
#
# Check 6 (the version is not already published) shells out to
# `gh release view`. Override what it runs by setting
# RELEASE_PREFLIGHT_GH_RELEASE_VIEW to a command, word-split and invoked as
# `$RELEASE_PREFLIGHT_GH_RELEASE_VIEW <tag>`; the default is
# `gh release view --repo lgw4/cetools --json id`. This is how the first five
# checks are exercised from pytest without `gh`, a token, or a network.
set -eu

if [ $# -ne 3 ]; then
    echo "usage: release-preflight.sh <tag> <pyproject-path> <changelog-path>" >&2
    exit 2
fi

tag="$1"
pyproject="$2"
changelog="$3"

if [ ! -f "$pyproject" ]; then
    echo "usage: release-preflight.sh: $pyproject not found" >&2
    exit 2
fi
if [ ! -f "$changelog" ]; then
    echo "usage: release-preflight.sh: $changelog not found" >&2
    exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Check 1: tag shape -- one `v` followed by YYYY.0M.INC1.
if ! printf '%s\n' "$tag" | grep -Eq '^v[0-9]{4}\.(0[1-9]|1[0-2])\.[1-9][0-9]*$'; then
    echo "tag $tag is not v<YYYY.0M.INC1>" >&2
    exit 1
fi
declared_from_tag=${tag#v}

# Check 2: the tag agrees with the declared version, read from the [project]
# table specifically so a same-named key under [tool.*] cannot shadow it.
version=$(awk '
/^\[/ { in_project = ($0 == "[project]") }
in_project && /^version[[:space:]]*=/ {
    match($0, /"[^"]*"/)
    print substr($0, RSTART + 1, RLENGTH - 2)
    exit
}
' "$pyproject")

if [ "$declared_from_tag" != "$version" ]; then
    echo "tag $tag does not match the declared version $version" >&2
    exit 1
fi

# Checks 3 and 5: the changelog has a section for the version, non-empty.
if ! body=$("$script_dir/changelog-section.sh" "$version" "$changelog" 2>/dev/null); then
    echo "no changelog section for version $version in $changelog" >&2
    exit 1
fi

if [ -z "$(printf '%s' "$body" | tr -d '[:space:]')" ]; then
    echo "changelog section for version $version is empty in $changelog" >&2
    exit 1
fi

# Check 4: the section is dated, not marked unreleased.
escaped_version=$(printf '%s' "$version" | sed 's/[.[\*^$]/\\&/g')
heading=$(grep -E "^## ${escaped_version}([[:space:]]|\$)" "$changelog" | head -n 1)

if printf '%s' "$heading" | grep -q '(unreleased)'; then
    echo "changelog section for version $version is marked (unreleased) in $changelog" >&2
    exit 1
fi
if ! printf '%s' "$heading" | grep -Eq '[0-9]{4}-[0-9]{2}-[0-9]{2}'; then
    echo "changelog section for version $version carries no date in $changelog" >&2
    exit 1
fi

# Check 6: the version is not already published, failing closed when the
# question could not be answered (FR-025).
view_cmd=${RELEASE_PREFLIGHT_GH_RELEASE_VIEW:-gh release view --repo lgw4/cetools --json id}
set +e
view_err=$($view_cmd "$tag" 2>&1 1>/dev/null)
view_status=$?
set -e
if [ "$view_status" -eq 0 ]; then
    echo "version $version is already published (release $tag exists)" >&2
    exit 1
fi
trimmed_view_err=$(printf '%s' "$view_err" | tr -d '[:space:]')
if [ "$trimmed_view_err" != "releasenotfound" ]; then
    echo "could not determine whether version $version is already published: $view_err" >&2
    exit 1
fi

exit 0
