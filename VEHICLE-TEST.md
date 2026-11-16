# Owner-approved vehicle test: Auto Seat 2.0

No vehicle changes have been performed by development or CI.
Do not use the old MIGRATION-UNTESTED-USB installer to migrate.
Keep the vehicle parked throughout testing and record each result.

## First stage: read-only preflight (requires Josh's agreement to start vehicle testing)

1. Download the artifact for the exact passing PR commit. Inside it choose
   `Ioniq5-auto-seat-2.0-PREFLIGHT-USB.zip`, not the inner install ZIP.
2. On Windows, use `Get-FileHash .\Ioniq5-auto-seat-2.0-PREFLIGHT-USB.zip -Algorithm SHA256`
   and compare the hash to the same artifact's SHA256SUMS.txt.
3. Extract the preflight ZIP to an empty USB drive. Its NEMESIS.data, migrate.sh,
   original.zip, candidate.zip and actions folder must be at USB root.
   Do not add NEMESIS.emergency or change the default descriptor.
4. Photograph every Auto Seat setting, including temperature unit, thresholds, both
   seats, wheel, startup and diagnostics. Close Auto Seat. Photograph NEMESIS's version,
   My Packages and Services, and the head-unit firmware/build information.
5. With Android fully started and the vehicle parked, insert the USB and approve
   the execute prompt. This default action only checks; it does not uninstall,
   install, stop a service or write settings.
6. Capture the result. Use NEMESIS Logs / Copy to USB if needed. Send the result,
   NEMESIS version and photos for review. A failure is a stop, not permission to bypass it.

Do not proceed past this stage without a separate approval for the migration.

## Approved migration stage (not authorized by creating these files)

Keep the exact same complete kit and its checksum. Do not edit the payloads.
After approval, replace USB-root NEMESIS.data with a copy of
`actions/MIGRATE.data` (keep the filename NEMESIS.data).
Reinsert and confirm execution. This action removes the old NEMESIS package and its
Android installation only after verified backups; it installs the original signed APK
under the new package metadata.

On success the HOLD remains active. Do not press Apply or Save or reboot yet.
Open Auto Seat only to compare all displayed settings to the photos.
Copy logs and the entire private `/data/nemesis/backup/auto-seat-migration-v1`
snapshot to a trusted PC through an approved root/file-access method if available.
The snapshot is not in the GitHub artifact; it is created only on your head unit.
Do not upload personal diagnostics or settings publicly.

## Acceptance and hardware stage (separate approval)

After settings and logs are reviewed, use `actions/ACCEPT.data` as root NEMESIS.data,
reinsert and confirm. Acceptance clears HOLD but sends no controls or service-start request.
Only after approval, reboot normally and verify exactly one package (`auto-seat`) and
one service (`auto-seat/apply`). The legacy helper directory alone is expected.

While parked, test each seat's isolated Heat, Vent and Off and check the factory indicators.
Confirm the other seat/wheel are unaffected. Verify Save/close/reopen persistence,
startup thresholds and manual priority. Do not infer actuator success from a shell exit alone.

## Approved rollback drill / recovery

A recovery rehearsal is required before store publication. It restores settings as of
the migration snapshot, so record any later desired changes first.
After approval, use `actions/RECOVER.data` as root NEMESIS.data, reinsert and confirm.
It restores the original `coldstart.heat` package, exact APK and snapshot settings.
Verify original settings, package/service count and APK/app function, then perform an
approved normal reboot to verify original startup behavior.

If any stage fails, keep the kit and backups unchanged and return the exact log.
Do not retry migration, manually uninstall either package, wipe NEMESIS, force-uninstall,
force-clear locks, remove orphan directories or change the firmware guard.
A partial snapshot without READY cannot authorize removal. A corrupted snapshot or
unknown orphan needs review. A damaged NEMESIS core, filesystem or Android system is
outside this package's recovery scope.

Record: exact commit/artifact/hash; firmware; NEMESIS version; preflight; settings match;
migration result; post-reboot package/service count; each control; startup/manual priority;
rollback result; rollback reboot; owner's final decision.
