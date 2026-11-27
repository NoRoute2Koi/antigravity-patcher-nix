#!/usr/bin/env bash
set -euo pipefail

VERSION="1.13.0"
PUBLISHER="Google"
NAME="google-antigravity"
VSIX_URL="https://open-vsx.org/api/${PUBLISHER}/${NAME}/${VERSION}/file/${PUBLISHER}.${NAME}-${VERSION}.vsix"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_VSIX="${1:-${SCRIPT_DIR}/${PUBLISHER}.${NAME}-${VERSION}-patched.vsix}"

for cmd in curl unzip zip python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "error: missing required command: $cmd" >&2
    exit 1
  fi
done

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

raw_vsix="$workdir/raw.vsix"
unpack_dir="$workdir/unpacked"

echo "Downloading ${PUBLISHER}.${NAME} v${VERSION}..."
curl -fsSL "$VSIX_URL" -o "$raw_vsix"

echo "Unpacking VSIX..."
unzip -q "$raw_vsix" -d "$unpack_dir"

ext_js="$unpack_dir/extension/extension.js"
if [ ! -f "$ext_js" ]; then
  echo "error: extension/extension.js not found in VSIX" >&2
  exit 1
fi

echo "Patching extension.js..."
python3 "$SCRIPT_DIR/scripts/patch.py" vscode "$ext_js"

echo "Packing patched VSIX -> $OUT_VSIX"
out_abs="$(realpath -m "$OUT_VSIX")"
(cd "$unpack_dir" && zip -qr "$out_abs" .)

echo "Done: $out_abs"
