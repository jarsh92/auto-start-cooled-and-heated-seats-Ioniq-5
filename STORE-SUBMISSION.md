# NEMESIS submission draft — held for vehicle validation and owner approval

> **AI-written Auto Seat changes · No human code review.** Developed with OpenAI ChatGPT/Codex under Josh Waldmire’s direction. Original upstream authorship is credited below.

| Portal field | Proposed value |
| --- | --- |
| Package ID | auto-seat (confirm portal availability before upload) |
| Display name | Auto Seat |
| Version | 2.0 |
| Short description | Temperature-based startup heat and ventilation |
| Source | https://github.com/jarsh92/auto-start-cooled-and-heated-seats-Ioniq-5 |
| License | MIT; retain LICENSE and CREDITS.md |
| Upload | Inner Ioniq5-auto-seat-2.0-MIGRATION-UNTESTED.zip after validation |
| Compatibility | Owner-tested app on US 2023 Hyundai Ioniq 5 Gen5W, supported seat equipment, exact build eng.vmadmin.20260903.161833 |
| Conflict | coldstart.heat |
| Android app identity | com.nemesis.coldstart, original signed 2.0 / 13 |

Description: Automatically apply configured seat heating, steering-wheel heating and
seat ventilation at startup based on outside temperature. Includes individual seat
controls, separate heating and ventilation settings, temperature units and optional
diagnostics. Only configured/equipped functions are supported.

Do not claim support for EU vehicles, ccNC, other model years/firmware or all trims.
Descriptor os/models currently use wildcards; the strict firmware preinstall guard
remains mandatory. Confirm portal compatibility values so the catalog does not imply
broad support. Confirm the ID is available.

Existing coldstart.heat users must use the separate verified migration kit; this
store ID is not a same-ID update. Do not tell them to uninstall first without backups.
New installs and same-ID auto-seat upgrades also need validation before public release.

## AI development disclosure

Auto Seat's additions and modifications to the upstream project—including its interface, expanded controls, migration scripts and packaging—were written by OpenAI's ChatGPT/Codex AI under Josh Waldmire's direction. Josh supplied requirements and reported vehicle behavior; he has not independently reviewed or verified the source code as a human programmer. No independent human programmer has reviewed or verified these Auto Seat changes.

Automated checks and owner-reported vehicle testing are not a human code review or independent verification of correctness, safety or reliability. The new package migration remains unverified on the actual head unit. Original upstream code remains credited to Gregory Taylor (eclipseempire); this AI disclosure does not attribute his work to AI or imply his review or endorsement of the changes.

Include this disclosure in the store listing and maintainer submission. Do not describe the Auto Seat changes as human-reviewed or independently verified unless a documented human review takes place.

## Release gates

- Passing CI at the exact submitted commit and archived SHA256SUMS.
- APK byte identity, original signer and KitKat v1 verification.
- Review of generated inner ZIP, source, helper bridge and checksum manifest.
- Owner-approved preflight and migration on the actual installed NEMESIS version.
- All settings preserved, one registered package/service, reboot/startup/manual priority.
- Owner-approved recovery drill restores original package and settings, including reboot.
- Fresh install, same-ID update and uninstall lifecycle validation.
- Owner approval to publish and portal metadata/ID confirmation.

Candidate names remain MIGRATION-UNTESTED until vehicle evidence supports promotion.
The final upload must contain NEMESIS.data at ZIP root. Never upload the outer Actions
artifact, preflight kit or source ZIP as the application package.
Use https://portal.xwtk.cloud/nemesis after the gates pass.
Nothing in CI submits to the portal, creates a public release, or merges this PR.
