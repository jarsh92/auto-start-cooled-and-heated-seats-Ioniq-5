#!/bin/bash
# Build + sign the Auto Seat settings APK (com.nemesis.coldstart).
#
# Requirements:
#   - A JDK (javac, keytool)
#   - Android build-tools (aapt, dx, zipalign, apksigner) and a platform android.jar
#
# Set these env vars (defaults assume a standard SDK layout):
#   ANDROID_SDK   path to your Android SDK root        (required)
#   BUILD_TOOLS   build-tools version   (default 30.0.3 - must still ship `dx`)
#   PLATFORM      platform for android.jar (default android-30)
#
# NOTE: this uses the legacy `dx` dexer, not `d8`. `d8`/`r8` from older
# build-tools crash under very new JDKs (e.g. JDK 27). `dx` emits DEX 035,
# which the KitKat-based Gen5W head unit requires anyway.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${ANDROID_SDK:?set ANDROID_SDK to your Android SDK root}"
: "${BUILD_TOOLS:=30.0.3}"
: "${PLATFORM:=android-30}"
BT="$ANDROID_SDK/build-tools/$BUILD_TOOLS"
AJ="$ANDROID_SDK/platforms/$PLATFORM/android.jar"
APP="$ROOT/app"
OUT="$APP/build"
KS="$APP/debug.jks"
: "${SIGNING_KEY:?Original installed APK signing key required; no replacement key will be generated}"
: "${KEY_ALIAS:?Set KEY_ALIAS for the original signing key}"
KS="$SIGNING_KEY"
[ -f "$KS" ] || { echo "Original signing key not found: $KS"; exit 1; }

[ -x "$BT/dx" ] || { echo "no dx in $BT (use a build-tools that still ships dx, e.g. 30.0.3)"; exit 1; }
[ -f "$AJ" ] || { echo "no android.jar at $AJ"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT/classes"

echo "== javac =="
java com.sun.tools.javac.Main -source 8 -target 8 -bootclasspath "$AJ" -d "$OUT/classes" $(find "$APP/src" -name '*.java')

echo "== dex (dx, min-sdk 19) =="
"$BT/dx" --dex --min-sdk-version=19 --output="$OUT/classes.dex" "$OUT/classes"

echo "== package manifest =="
"$BT/aapt" package -f -M "$APP/AndroidManifest.xml" -S "$APP/res" -I "$AJ" -F "$OUT/base.apk"
( cd "$OUT" && "$BT/aapt" add base.apk classes.dex >/dev/null )

echo "== align =="
"$BT/zipalign" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"

echo "== sign (v1 required for KitKat) =="
: "${SIGNING_STORE_PASSWORD:?Set SIGNING_STORE_PASSWORD privately}"
: "${SIGNING_KEY_PASSWORD:?Set SIGNING_KEY_PASSWORD privately}"
"$BT/apksigner" sign --ks "$KS" --ks-key-alias "$KEY_ALIAS" \
  --ks-pass env:SIGNING_STORE_PASSWORD --key-pass env:SIGNING_KEY_PASSWORD \
  --v1-signing-enabled true --v2-signing-enabled true --min-sdk-version 19 \
  --out "$APP/auto-seat.apk" "$OUT/aligned.apk"

# Refuse to package an APK Android cannot install over the existing app.
EXPECTED=6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59
ACTUAL=$("$BT/apksigner" verify --print-certs "$APP/auto-seat.apk" | sed -n 's/^Signer #1 certificate SHA-256 digest: //p' | tr 'A-F' 'a-f')
if [ "$ACTUAL" != "$EXPECTED" ]; then
  rm -f "$APP/auto-seat.apk"
  echo "Signing certificate differs from the installed 1.6.0 app; no update APK retained."
  exit 1
fi

echo "== done: $APP/auto-seat.apk =="
"$BT/aapt" dump badging "$APP/auto-seat.apk" 2>/dev/null | grep -E "package|sdkVersion" | head
echo "Copy app/auto-seat.apk to package/app/auto-seat.apk, then build the NEMESIS zip."
