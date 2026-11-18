# Build and inspect Auto Seat — AI-written packaging

Current package: `autoseat.heat`. The migration builder is retired. No signing key is needed because packaging copies the original signed APK from the checksum-pinned original release ZIP.

1. Use Python 3.9+ and a POSIX shell for regression checks. Java 17 is needed for the command-generation tests.
2. Run `python3 tools/package_release.py` and `python3 tests/check_clean_install.py`, plus `python3 tests/check_commands.py` and `python3 tests/check_startup_priority.py` on a POSIX host.
3. Release CI additionally installs Android build-tools 30.0.3 and runs the builder with `--verify-signature`, requiring ANDROID_HOME or ANDROID_SDK and apksigner. It verifies the expected certificate, KitKat v1 signature and DEX 035. Packaging does not rebuild or re-sign the app.
4. `dist/` contains the USB installer, inner NEMESIS package, public source ZIP, SHA256SUMS.txt and validation record. Only the USB ZIP is the vehicle installer.

`verification/vehicle-tested-runtime-sha256.json` pins the runtime files of the clean build tested by the owner. Metadata, APK, hooks, helper, startup and USB scripts must match; credits/instructions may change independently. A runtime change is a new build needing appropriate validation.

Android app source changes still need a compatible toolchain and original signing identity for an in-place update. That private key has not been recovered and is not in the repository. `tools/build_apk.sh` remains a separate development path; it must not silently replace the immutable release app. The release builder generates no key or replacement identity.

Local Windows tests use portable BusyBox and fake Android responses. POSIX CI can test host permission-mask behavior; neither is the head unit. Tests do not connect to a vehicle.

This post was prepared and posted with ChatGPT.
