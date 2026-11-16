# Auto Seat 2.0 migration candidate

Status: automated migration/recovery checks passed; awaiting an owner-approved vehicle preflight.
See [MIGRATION-VALIDATION.md](MIGRATION-VALIDATION.md) for evidence and limits.
Do not submit to the NEMESIS store until vehicle migration and recovery have passed.
The original published v2.0 downloads remain unchanged.

## Identities and unchanged binary

| Item | Value |
| --- | --- |
| NEMESIS old / new | `coldstart.heat` / `auto-seat` |
| Android package | `com.nemesis.coldstart` |
| Android version / code | 2.0 / 13 |
| Persistent settings | `/data/nemesis/state/coldstart.heat` |
| Shared lock | `/dev/seat-comfort/actuation.lock` |
| Firmware guard | `eng.vmadmin.20260903.161833` |
| Original release ZIP SHA-256 | `32d6e014421bc2ff1104de3c004079377c39b8e62eae0e1c6f2d470e9aefb5ad` |
| Original APK SHA-256 | `97a181a2289ac31285d8347964dfeba7e6982da7447968886dc53d5302b7ad3b` |
| Signer certificate SHA-256 | `6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59` |

Packaging verifies the release checksum, the signature and the signer, and copies the exact APK bytes.
There is no signing operation or replacement key. Source compilation is a separate check.

## Compatibility bridge

The immutable APK hard-codes
`/data/nemesis/apps/coldstart.heat/scripts/seat-action.sh`.
The new postinstall creates only that helper and an ownership marker at the legacy path.
This is a compatibility directory, not a second NEMESIS package: it has no descriptor or service.
The helper is byte-identical to the new package helper. Both use the same settings and actuation lock.
The new preinstall rejects any existing legacy directory. NEMESIS conflict metadata rejects
a registered `coldstart.heat` in either direction.
The new preuninstall removes only a marked, strictly allowlisted owned bridge (including an interrupted helper copy). It never recursively removes an unknown legacy tree.
No hook uninstalls another package or edits packages.db/services.db.

## Migration transaction

`migration/migrate.sh` defaults to `check`, which does not stop services, close the app,
change settings, install, uninstall or create a backup. It verifies the firmware, fully
started Android, root access, toolbox commands, exact original installed package tree,
original installed APK bytes, state tree and exactly one old service. Only the published
original 2.0 is supported. Older, modified or unknown uninstall hooks fail closed.

Mutation requires a separate action and explicit token. It acquires the shared actuation lock,
records manual priority, stops the old service, closes the app, and creates a new transaction at
`/data/nemesis/backup/auto-seat-migration-v1`. Existing transactions are never overwritten.
It makes two independently copied, byte-compared state snapshots (including hidden/nested
regular files), saves the original reinstallable ZIP, syncs, and marks READY.
Symlinks and special files are rejected. State is private root-owned data; restored bytes
are preserved, while file modes use the migration's private umask.

Only after READY does it use supported `nemesis uninstall coldstart.heat`.
The published original descriptor has no uninstall hooks; NEMESIS removes its Android
APK as part of normal uninstall. This is why the separate recovery archive and external
settings snapshot are mandatory. The app stores its settings in that external state tree;
Android's private app directory is not treated as its settings store.

It restores and verifies state before `nemesis install candidate.zip`.
The new service and write/actuation helper honor a durable HOLD outside either package tree.
It verifies the APK, complete installed tree, helper bridge, settings bytes, package registry
and exactly one new service. HOLD survives reboot and failures. Read-only settings display
remains available. Acceptance requires another explicit command and checks, clears HOLD,
and does not start services or send actuator calls.

## Recovery and interruption

Recovery requires READY and matching snapshot copies and recovery ZIP.
It takes the same lock, holds/stops the new package if present, removes it through NEMESIS,
restores settings first, and reinstalls the original signed package only if absent.
After original reinstall, it restores the exact snapshot again because original postinstall can seed absent defaults. An already registered original is verified rather than overwritten.
It then checks original APK, original tree, settings and single service.
The manual-priority marker suppresses startup actuation in the current boot.
The snapshots are retained.

Failures stop with logs and keep the snapshot. Never use --force, edit registries, replace
a signing key, bypass the firmware guard, delete the snapshot, or force-clear an actuation lock.
Unknown orphan directories, mismatched old files, damaged bridge ownership, mismatching
backup copies and an incomplete snapshot require review; recovery does not guess or delete them.
A power cut before READY leaves the original package installed. After READY, use recovery,
not another migrate run. An interrupted lock may require an approved normal reboot;
the new HOLD remains effective across it. Do not reboot or relaunch the old package mid-transaction.

## Validation boundary

Host tests execute the real migration and lifecycle shell code with fake NEMESIS/Android
commands and temporary files. They verify transaction ordering and failure behavior, not
the head unit's actual NEMESIS version, toolbox behavior, power-loss guarantees or hardware.
Recovery is automatically verified in simulation; it is not yet vehicle-verified.
Follow [VEHICLE-TEST.md](VEHICLE-TEST.md) only after the owner approves vehicle testing.
[STORE-SUBMISSION.md](STORE-SUBMISSION.md) describes the held submission.

Upstream behavior was reviewed from:
- https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md
- https://github.com/xwtk/hmg_nemesis/blob/main/06-Run-Scripts.md
- https://github.com/xwtk/hmg_nemesis/blob/main/NEMESIS%20Source/native/pkg.c
- https://github.com/xwtk/hmg_nemesis/blob/main/NEMESIS%20Source/native/svc.c

The upstream source can differ from the installed version; that is a vehicle-test gate.
