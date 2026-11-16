# Auto Seat 2.0 migration validation record

## Evidence reviewed

Original PR head: `310cb22fefdc049a3d4566ce4f27817fae62370a`.
Original successful run: https://github.com/jarsh92/auto-start-cooled-and-heated-seats-Ioniq-5/actions/runs/43977200544
(all three jobs passed).

Retrieved artifact: `auto-seat-2.0-MIGRATION-UNTESTED`, ID `14281222235`.
Original artifact ZIP SHA-256:
`213151f7eb95b483baa34cd076ff9d44e2a778c145f4ea93cb039ac6918cabd0`.

Historical artifact was downloaded and opened inside GitHub Actions after the local
execution tool reported no usable environment. The initial cross-host redirect kept
an Authorization header and produced HTTP 401; the inspector was corrected to remove
that header on redirect, then rerun successfully.
Inspection evidence:
https://github.com/jarsh92/auto-start-cooled-and-heated-seats-Ioniq-5/actions/runs/43979458559

The inspector verified the artifact digest, opened its nested application archive,
compared its APK with the immutable original release, and printed its descriptor and
archive entries. It found no helper bridge in that historical package. The unchanged
APK's absolute helper path would therefore break after changing the package ID.
It also found literal backslash-n sequences in the generated README; these are fixed.

## Current automated validation

Code commit:
`8ea9365319ee787371c44648a9ae791a68f992f4`.

Validation run:
https://github.com/jarsh92/auto-start-cooled-and-heated-seats-Ioniq-5/actions/runs/43980006962

Later documentation/packaging commits are checked by the same workflow at PR #2.
Use the newest passing commit's artifact rather than mixing files across runs.

| Check | Result |
| --- | --- |
| Original signed APK bytes and signer | Passed; copied without rebuilding or signing |
| KitKat v1 signature and DEX 035 | Passed |
| Java compile and KitKat-compatible DEX generation | Passed, unsigned source check only |
| 48 original command combinations + 8 isolated heat levels | Passed |
| Shared lock, Off, invalid values, read/save, error cleanup | Passed |
| Delayed startup/manual priority; normal ventilation | Passed |
| Default read-only preflight and missing token | Passed; installation/settings unchanged |
| Firmware/Android/APK/descriptor/service/link/lock/snapshot gates | Passed |
| Migration preserves all setting bytes, including hidden/nested/unknown and absent files | Passed |
| Old absolute APK helper path bridge | Passed; one registered package/service |
| HOLD blocks startup, controls and Save; read remains available | Passed |
| Backup, uninstall, install and postinstall failures | Passed; stop and recover where snapshot complete |
| Failed recovery reinstall retry | Passed without replacing snapshot |
| Corrupt snapshot and unknown orphan | Passed; refuse destructive recovery |
| Interrupted owned helper copy and unknown bridge files | Passed; recover owned copy, retain unknown files |
| Modified new uninstall hook | Passed; reject before removal |
| Simulated reboot then recovery | Passed |
| Fresh install, same-ID update, uninstall real shell hooks | Passed in fake NEMESIS harness |
| Nested ZIP layout, docs/source inclusion, checksums, secret exclusion | Passed |

Host tests use the real shell scripts and fake Android/NEMESIS commands. They are
not an emulator of the exact installed NEMESIS binary and do not prove actual
head-unit behavior, storage durability under power loss, or vehicle actuator response.

## Remaining gates

Vehicle preflight, migration, UI/settings comparison, actual reboot/service count,
parked actuator checks, startup/manual priority and a rollback drill remain pending
owner approval and execution. Recovery is verified in simulation only.
Store publication remains held; no portal upload or vehicle modification has occurred.

Original published release files remain unchanged in downloads/ and release v2.0.
All development code, migration/recovery documentation and workflow are committed
to the existing PR branch. Generated artifacts are rebuildable from committed inputs;
the workflow retains artifacts for 90 days.
