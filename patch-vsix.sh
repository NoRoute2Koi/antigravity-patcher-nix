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
curl -fsSL --retry 3 "$VSIX_URL" -o "$raw_vsix"

echo "Unpacking VSIX..."
unzip -q "$raw_vsix" -d "$unpack_dir"
chmod -R u+w "$unpack_dir"

ext_js="$unpack_dir/extension/extension.js"
if [ ! -f "$ext_js" ]; then
  echo "error: extension/extension.js not found in VSIX" >&2
  exit 1
fi

echo "Patching extension.js..."
python3 "$SCRIPT_DIR/scripts/patch.py" vscode "$ext_js"

# Strip invalidated digital signature metadata so VS Code / VSCodium accepts the repacked VSIX.
rm -rf "$unpack_dir/package" "$unpack_dir/_rels"
if [ -f "$unpack_dir/[Content_Types].xml" ]; then
  python3 -c '
import sys, re
from pathlib import Path
p = Path(sys.argv[1])
xml = p.read_text(encoding="utf-8")
xml = re.sub(r"\s*<Default\b[^>]*digital-signature[^>]*/>\s*", "\n  ", xml)
xml = re.sub(r"\s*<Default\b[^>]*Extension=\"rels\"[^>]*/>\s*", "\n", xml)
p.write_text(xml, encoding="utf-8")
' "$unpack_dir/[Content_Types].xml"
fi

echo "Packing patched VSIX -> $OUT_VSIX"
out_abs="$(realpath -m "$OUT_VSIX")"
rm -f "$out_abs"
(cd "$unpack_dir" && zip -qr "$out_abs" .)

echo "Done: $out_abs"
