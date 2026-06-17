#!/usr/bin/env bash

set -e

JSON_MODE=false
DRY_RUN=false
SHORT_NAME=""
BRANCH_NUMBER=""
USE_TIMESTAMP=false
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json) JSON_MODE=true ;;
        --dry-run) DRY_RUN=true ;;
        --short-name)
            i=$((i + 1))
            next="${!i}"
            [[ -z "$next" || "$next" == --* ]] && { echo 'Error: --short-name requires a value' >&2; exit 1; }
            SHORT_NAME="$next"
            ;;
        --number)
            i=$((i + 1))
            next="${!i}"
            [[ -z "$next" || "$next" == --* ]] && { echo 'Error: --number requires a value' >&2; exit 1; }
            BRANCH_NUMBER="$next"
            ;;
        --timestamp) USE_TIMESTAMP=true ;;
        --help|-h)
            echo "Usage: $0 [--json] [--dry-run] [--short-name <name>] [--number N] [--timestamp] <feature_description>"
            exit 0
            ;;
        *) ARGS+=("$arg") ;;
    esac
    i=$((i + 1))
done

FEATURE_DESCRIPTION="${ARGS[*]}"

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

clean_branch_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

generate_branch_name() {
    local description="$1"
    local stop_words="^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"
    local clean_name
    clean_name=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')
    local meaningful_words=()
    for word in $clean_name; do
        [ -z "$word" ] && continue
        if ! echo "$word" | grep -qiE "$stop_words" && [ ${#word} -ge 3 ]; then
            meaningful_words+=("$word")
        fi
    done
    if [ ${#meaningful_words[@]} -gt 0 ]; then
        local max_words=3
        [ ${#meaningful_words[@]} -eq 4 ] && max_words=4
        local result="" count=0
        for word in "${meaningful_words[@]}"; do
            [ $count -ge $max_words ] && break
            [ -n "$result" ] && result="$result-"
            result="$result$word"
            count=$((count + 1))
        done
        echo "$result"
    else
        clean_branch_name "$description" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

get_highest_from_specs() {
    local specs_dir="$1"
    local highest=0
    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            if echo "$dirname" | grep -Eq '^[0-9]{3,}-' && ! echo "$dirname" | grep -Eq '^[0-9]{8}-[0-9]{6}-'; then
                number=$(echo "$dirname" | grep -Eo '^[0-9]+')
                number=$((10#$number))
                [ "$number" -gt "$highest" ] && highest=$number
            fi
        done
    fi
    echo "$highest"
}

REPO_ROOT=$(get_repo_root)
cd "$REPO_ROOT"
SPECS_DIR="$REPO_ROOT/specs"

if [ -n "$SHORT_NAME" ]; then
    BRANCH_SUFFIX=$(clean_branch_name "$SHORT_NAME")
elif [ -n "$FEATURE_DESCRIPTION" ]; then
    BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
else
    echo "Error: provide a feature description or --short-name" >&2
    exit 1
fi

if [ "$USE_TIMESTAMP" = true ] && [ -n "$BRANCH_NUMBER" ]; then
    echo "[specify] Warning: --number is ignored when --timestamp is used" >&2
    BRANCH_NUMBER=""
fi

if [ "$USE_TIMESTAMP" = true ]; then
    FEATURE_NUM=$(date +%Y%m%d-%H%M%S)
    BRANCH_NAME="${FEATURE_NUM}-${BRANCH_SUFFIX}"
else
    if [ -z "$BRANCH_NUMBER" ]; then
        HIGHEST=$(get_highest_from_specs "$SPECS_DIR")
        BRANCH_NUMBER=$((HIGHEST + 1))
    fi
    FEATURE_NUM=$(printf "%03d" "$((10#$BRANCH_NUMBER))")
    BRANCH_NAME="${FEATURE_NUM}-${BRANCH_SUFFIX}"
fi

if [ "$DRY_RUN" != true ]; then
    if ! git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
        echo "Error: not a git repository" >&2
        exit 1
    fi

    if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
        echo "[specify] Branch '$BRANCH_NAME' already exists; switching to it" >&2
        git -C "$REPO_ROOT" checkout "$BRANCH_NAME"
    else
        git -C "$REPO_ROOT" checkout -b "$BRANCH_NAME"
        echo "[specify] Created and switched to branch: $BRANCH_NAME" >&2
    fi
fi

if $JSON_MODE; then
    if command -v jq >/dev/null 2>&1; then
        jq -cn --arg bn "$BRANCH_NAME" --arg fn "$FEATURE_NUM" \
            '{BRANCH_NAME:$bn,FEATURE_NUM:$fn}'
    else
        printf '{"BRANCH_NAME":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$FEATURE_NUM"
    fi
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "FEATURE_NUM: $FEATURE_NUM"
fi
