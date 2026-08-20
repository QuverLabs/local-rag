#!/bin/sh
set -eu

usage() {
    echo "Usage: $0 [--config /path/to/claude_desktop_config.json] /path/to/markdown" >&2
    exit 2
}

config_path=
notes_arg=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config)
            [ "$#" -ge 2 ] || usage
            config_path=$2
            shift 2
            ;;
        -*) usage ;;
        *)
            [ -z "$notes_arg" ] || usage
            notes_arg=$1
            shift
            ;;
    esac
done

[ -n "$notes_arg" ] && [ -d "$notes_arg" ] || usage
notes_dir=$(cd "$notes_arg" && pwd -P)
if ! find "$notes_dir" -type f -name '*.md' -print -quit | grep -q .; then
    echo "No Markdown files found below $notes_dir" >&2
    exit 1
fi

if [ -z "$config_path" ]; then
    if [ "$(uname -s)" != Darwin ]; then
        echo "Use --config to provide the MCP client config path on this system." >&2
        exit 1
    fi
    config_path="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
fi

config_dir=$(dirname "$config_path")
config_name=$(basename "$config_path")
mkdir -p "$config_dir"
config_dir=$(cd "$config_dir" && pwd -P)

docker_command=$(command -v docker || true)
if [ -z "$docker_command" ]; then
    echo "Docker not found. Install and start Docker Desktop." >&2
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Start Docker Desktop." >&2
    exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(dirname "$script_dir")
image=local-rag:dev

docker build --platform linux/amd64 -t "$image" "$repo_dir"
docker run --rm \
    --platform linux/amd64 \
    --user "$(id -u):$(id -g)" \
    --entrypoint python \
    --mount "type=bind,source=$config_dir,target=/claude" \
    "$image" -m setup.install_claude_desktop \
    --docker \
    --config-path "/claude/$config_name" \
    --docker-command "$docker_command" \
    --notes-dir "$notes_dir"
