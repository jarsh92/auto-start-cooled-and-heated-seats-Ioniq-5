# Auto Seat 2.0 — startup confirmation and retry RC2 CANDIDATE

AI-written with ChatGPT/Codex under Josh Waldmire's direction.
NOT YET VEHICLE-TESTED. No independent human code review completed.
This is a public test candidate, not a stable release or store upload.

The UI, Android APK, signing certificate, version 2.0, package `autoseat.heat`
and saved-state location are unchanged. Only the startup service executable
differs from the owner-tested runtime. This candidate rejects uncorroborated
ECO -40°C and prefers fresh ready dashboard readings. It confirms the requested
action rather than an identical temperature, so 47°F to 55°F can still confirm
heating. A short-lived live capture retains brief temperature messages. If the
first attempt remains undecided, one retry runs at about 3–4 minutes after
service entry. A final timeout leaves the seats unchanged.

Once an action or neutral result is confirmed, it exits without a retry. Auto
Seat manual commands cancel pending automation. Factory seat/wheel button
changes are NOT detected: a delayed action could change a factory-selected
level. This limitation must be considered during parked testing.

Compatibility remains ONLY the intended US 2023 IONIQ 5 Limited Gen5W,
internal build `eng.vmadmin.20260903.161833`, with NEMESIS 1.16.7 as previously
tested. A user is separately updating NEMESIS; RC2 does not install or require
that update, and no test on the newer NEMESIS version is claimed yet. No EU,
ccNC, other trim or other firmware support is asserted.

## Owner test installation

This uses the same CLEAN installer as the current release. It is not an
in-place update: its firmware/helper safeguards deliberately refuse an already
installed seat package. Do not bypass them or delete directories manually.

Before proceeding, keep the current working release installer and export your
current diagnostics. Record your saved settings. While parked, use NEMESIS
My Packages to uninstall the current Auto Seat package, then extract ALL files
of the candidate USB ZIP onto an otherwise empty USB. Leave its inner ZIP
compressed. Insert the USB with Android fully started and approve Execute.
The normal uninstaller retains saved settings; review them after installation.
If installation fails, keep the logs and stop rather than retrying removals.

Check controls manually while parked, then use repeated cold/warm head-unit
starts to test automation. With heating below 62°F and ventilation above 67°F,
a trustworthy 73°F reading must choose ventilation, not heating; 62–67°F must
choose neither. Real warm weather or threshold changes for a deliberate parked
test may be needed. Restore your usual thresholds afterward.

Leave diagnostic logging enabled during the test. If automation does nothing,
use the manual controls and return the new diagnostic and NEMESIS service logs.
The fix intentionally waits for fresh records, so one car test cannot establish
reliability across all startup sequences. Do not mark this stable before review.

For rollback, uninstall through NEMESIS and reinstall the saved previous working
release using its normal instructions. The earlier bug is present in that
release; manual operation remains available.

Original project: Gregory Taylor (eclipseempire), HKMC Cold-start Heat, MIT.
Retain LICENSE and CREDITS.md. No original author endorsement is claimed.

This post was prepared and posted with ChatGPT.
