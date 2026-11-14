#!/bin/bash
# Build versioned NEMESIS, public source, and USB archives from the signed APK.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tools/package_release.py"
