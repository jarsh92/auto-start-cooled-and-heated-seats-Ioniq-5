# Auto Seat 2.0: NEMESIS store candidate

Status: draft source changes only. No store submission, rebuilt installer, or in-car migration validation has been completed. The published v2.0 USB installer still uses coldstart.heat. Do not upload that installer under the new name.

## Identity

- NEMESIS package ID: `auto-seat` (availability still requires confirmation in the portal).
- Display name: Auto Seat.
- App and package version: 2.0.
- Android package: `com.nemesis.coldstart`; retain the tested APK and its signing identity.
- Saved settings: `/data/nemesis/state/coldstart.heat`; retain this legacy location because the existing APK and service both use it.
- Keep the existing shared actuation lock and manual-override marker.
- Retain all upstream credits and the MIT license.

This branch contains the 2.0 source from commit `7680d2f227721fdbd64822f664296f8170de79bd` and changes package/NEMESIS.data to the new ID with a legacy-package conflict. The APK and service retain their existing internal identities.

The descriptor adds `depends=!coldstart.heat`. NEMESIS checks this conflict before installation and enforces it in both directions. A new package ID does not update or replace the old package automatically. The conflict prevents two registered startup services from coexisting.

## Migration preparation

Do not call `nemesis uninstall coldstart.heat` from the new package's install hooks. Do not install auto-seat and then uninstall coldstart.heat: the old uninstaller also removes the shared Android package.

Before distributing an installer, implement and validate a separate migration procedure that:

1. Confirms the exact supported head-unit build before making changes.
2. Checks the installed old package and its uninstall hooks.
3. Stops the old startup service while taking a verified backup of saved state. Saves a reinstallable copy of the existing package and the tested signed APK for recovery.
4. Removes the old NEMESIS package through its supported uninstall mechanism before installing auto-seat. Preserves and restores the saved state before the new startup service can run.
5. Checks each operation and stops on failure without forcing removal, editing registry databases, or disabling firmware checks.
6. Confirms there is one installed seat package and one registered startup service after installation and reboot.
7. Confirms saved heating, ventilation, temperature-unit, startup and diagnostic options match the backup, and validates real controls while parked.

This migration procedure is not yet implemented. Do not ask an owner to uninstall their working package until backup, restore and recovery have been validated.

## Build and submission requirements

- Keep the exact existing firmware guard: `eng.vmadmin.20260903.161833`.
- Describe compatibility as owner-tested on a US-market 2023 Hyundai Ioniq 5 Gen5W with NEMESIS and equipped seat functions; other cars, trims and firmware remain unverified. No EU or ccNC claim.
- The current os/models wildcards do not express these restrictions; the firmware preinstall guard remains mandatory. Confirm portal compatibility metadata before submitting.
- Adjust packaging instructions: the old text saying "Do not uninstall first" applies to same-ID updates, not this migration.
- Mark migration artifacts as untested candidates until the vehicle test passes. The earlier successful 2.0 UI test does not validate this new installer.
- Use a distinct candidate filename and retain the working public v2.0 assets.
- Upload the inner installable ZIP with NEMESIS.data at its root, not the outer USB/source bundle.
- Submit through https://portal.xwtk.cloud/nemesis with the public GitHub source URL and retained credits. A GitHub release alone does not submit a package to the store.

References:
- https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md
- https://github.com/xwtk/hmg_nemesis/blob/main/08-Submit-a-Package.md

## Signed APK provenance (store candidate)

The packaging script now reads the existing published `downloads/Ioniq5-auto-seat-2.0.zip` (expected SHA-256 `32d6e014421bc2ff1104de3c004079377c39b8e62eae0e1c6f2d470e9aefb5ad`), extracts its sole APK, verifies the APK signature and expected signer certificate SHA-256 `6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59`, and copies those exact APK bytes into the candidate package. No new key or signing operation is used. The original archive and release are not modified. The packaging script still requires an available Android SDK apksigner for verification.

A separate Maps HUD Suite private signing backup must **not** be assumed to belong to Auto Seat. Compare the public certificate fingerprint only, using `keytool -list -v -keystore /private/path/to/backup.jks` in a trusted private environment, and compare the SHA-256 to the Auto Seat expected fingerprint above. Never commit, upload, or expose keystore bytes or passwords. No matching backup has been verified in this workspace.
