#!/bin/sh
# Copies the secret guard into .githooks/ and points git at it.
# Run from the root of the repo you want to protect.
set -e
root=$(git rev-parse --show-toplevel)
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$root/.githooks"
cp "$here/pre-commit" "$root/.githooks/pre-commit"
chmod +x "$root/.githooks/pre-commit"
git -C "$root" config core.hooksPath .githooks
echo "Secret guard installed: core.hooksPath=.githooks"
