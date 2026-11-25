# Incorrect startup heating from an unready temperature

Status: confirmed in owner logs; proposed service fix and host tests prepared.
Initial owner feedback after candidate installation is positive. Repeated
on-vehicle startup validation and independent human code review are pending.
Auto Seat changes and this document were written with ChatGPT/Codex under
Josh Waldmire's direction. Original upstream authorship remains credited.

## Report and evidence

On November 22, 2026, Josh reported occasional missed startup actions and
heating instead of ventilation. He recalls a recent trip showing 73°F on the
dashboard. That observation cannot be matched conclusively to an individual
logged start: startup wall clocks often begin at January 1, 2015 before syncing.

The uploaded NEMESIS archive contains the current `autoseat.heat/apply.log`:

- 76 recorded service starts, not necessarily 76 driver trips.
- 39 ECO readings of `outTemperature=-40C=-40F` followed by heating commands.
- Three explicit temperature timeouts with no action.
- Some other starts end while waiting without a recorded outcome; their cause
  cannot be established from these files.
- On November 22 at the logged time 08:39:40, ECO -40 was accepted and the app
  issued wheel-on and driver heat enum 8. The actual outside temperature then
  is not recorded by an independent source in this excerpt.
- Thresholds are heat below 62°F and ventilation above 67°F. Readings from
  62°F through 67°F inclusive correctly choose neither.

The service log after the November 17 installation uses `autoseat.heat`.
Earlier `coldstart.heat` logs remain as history. NEMESIS records removal of the
old package before the newer service started, not concurrent seat services.

Josh recalls other people reporting similar behavior online. No original
posts, version details, or independent reproductions have been verified.
These reports are background only; do not attribute this confirmed defect to
every upstream version or claim the original author has acknowledged it.

## Cause and limits

The previous reader prioritized the newest ECO JSON value and accepted any
Celsius integer in [-50,60], including -40. The logs repeatedly show -40 soon
after a dashboard `temp=-1 / tempunit=-1` not-ready message. This strongly
suggests an initialization/sentinel value. The framework's exact contract has
not been independently established.

Once that value was accepted, the service issued heating commands and exited;
it did not reconsider a later correct dashboard value. The deadline counted
requested sleep seconds rather than actual elapsed time, so expensive logcat
scans made the logged 120-second limit misleading. Readiness waiting also
continued to temperature processing even if the VR check never succeeded.

Log command exit 0 does not independently prove actual seat actuation.
Head-unit wakes do not establish ignition/drive-ready status. Those are limits
of current evidence, not newly diagnosed causes of the reported trips.

## Proposed fix

1. Capture existing log records as a baseline before waiting for services.
   Only a subsequent distinct record can supply a startup temperature.
2. Prefer a fresh dashboard value with a ready explicit unit. Preserve the
   configured unit fallback only when the unit field is absent.
3. Reject uncorroborated ECO -40 and malformed values. A genuinely ready
   dashboard reading of -40 remains usable; do not treat all subzero weather
   as invalid. Parse signed decimals without accepting numeric prefixes.
4. Require the same source and integer-Fahrenheit candidate across polls at
   least three kernel-clock seconds apart. An invalid or changed sample
   resets confirmation. This is consistency of the latest observed record,
   not proof of two independent sensor measurements.
5. Read both sources in one logcat snapshot per poll. Use kernel uptime for
   real elapsed deadlines, unaffected by wall-clock synchronization. Refuse
   to act after readiness/temperature timeout; no default temperature or
   default heater action. An in-flight logcat call can overrun a deadline;
   its late result is rejected before actuation.
6. Check both control service registrations and preserve the existing
   manual-override marker and shared actuation lock. Log selected source,
   temperatures, ventilation settings, and uptime.

## Validation and vehicle checks

`python3 tests/check_startup_temperature.py` runs the actual service shell with
fake logcat, binder, paths and monotonic clock. Scenarios include -40 then 73°F,
conflicting sources, persistent -40, stale records, transient cold readings,
invalid samples, valid negative/Celsius temperatures, exact threshold bounds,
malformed JSON, missing/invalid units, disabled options, manual override,
late service registration and slow logcat/deadline handling.

The existing manual-command priority and clean-install lifecycle tests remain
required. Packaging must retain the exact signed APK and verify that the only
changed runtime file is the startup service; the vehicle-tested hash inventory
must not be relabeled to imply this candidate has already been vehicle-tested.

Before release, test repeated real cold/warm starts while parked, including a
ready reading above the ventilation threshold. Check actual factory indicators,
seat response, manual override, settings persistence and return new diagnostics.
The conservative fresh-record rule may leave the seats unchanged if this
firmware logs temperature only before the baseline and emits no later record.
That availability tradeoff requires car testing; do not silently restore the
old stale-value fallback. Vehicle-ready gating and actuation readback remain
separate future investigations.

## Initial owner feedback — November 22, 2026

After installing the candidate, Josh reported: “seems to have worked for now.
only time will tell.” This is initial positive owner feedback, not confirmation
that repeated cold and warm starts or every control path have passed. No new
post-fix diagnostic logs have been reviewed yet. Keep the fix as a draft test
candidate pending repeated starts and log review; the stable release is unchanged.

## November 23 follow-up: RC1 missed starts; RC2 refinement

The first post-fix diagnostic export contains 19 RC1 service runs: six issued
heating commands and 13 ended without a confirmed temperature action. These
are service runs, not 19 driving trips. At the logged time around 13:55, valid
dashboard readings of 47°F and 46°F were observed, but the run ended with
`no fresh stable outside temp ... no action`. Both readings call for heating
with the saved 62°F threshold. RC1 required the same integer temperature and
source; a change or missing record reset confirmation. The logs do not record
every rejected/missing poll, so their exact sequence cannot be reconstructed.

The firmware log buffer may also lose a short-lived temperature event between
polls. This is a plausible contributing mechanism, not a proven explanation for
all 13 timeouts. RC2 directly tests and addresses that case without falling back
to unready -40 readings.

RC2 supersedes the exact-temperature/source confirmation described above:

- Confirm the same requested **heat / ventilation / no-action** result over at
  least three kernel-clock seconds. A change such as 47°F to 55°F can confirm
  heat; crossing into a different action restarts confirmation.
- Retain a limited startup live capture from the two temperature source tags
  observed on the supported firmware, `SplitScreenClimateView` and `CoNA`.
  Exclude all pre-existing baseline records replayed by logcat. This avoids
  repeatedly scanning the full Android log buffer and retains brief events.
- A candidate is usable for at most 30 seconds after it was first observed by
  the polling loop, unless a distinct new valid record refreshes it. A missing
  record alone does not reset it; a new invalid dashboard event does. These
  checks do not establish the actual sensor acquisition time.
- Attempt startup normally, then allow one delayed retry starting at about
  180 seconds after service entry, ending at 240 seconds. Only undecided
  starts retry. Heating, ventilation, or a confirmed neutral result ends the
  service; it does not regulate seats continuously during the drive.
- The delayed window requires new records relative to its own baseline, not a
  cached first-attempt temperature. No fallback temperature or default heater
  command is introduced. Existing application manual priority remains active.
- Stop the listener and remove its volatile capture on completion, cancellation
  or a handled termination signal. If the listener exits, bounded snapshot
  polling remains available as a fallback.

**Manual-control limitation:** only commands through Auto Seat create the
existing manual-override marker. Factory seat/wheel button changes are not
detected by this service. A delayed automatic action could therefore change a
factory-selected level. Reliable factory-state/manual-input detection needs
separate validation; do not claim that RC2 handles it.

The 27 startup test methods include large same-action temperature changes,
source changes, short-lived/evicted records, late fresh data, delayed service
readiness, bounded final exit, no repeated action after success, manual
cancellation during the delay, and termination cleanup. Existing command and
package lifecycle checks remain required. These are host simulations, not car
validation. RC2 has not yet been tested on the vehicle.

The Android Auto black-screen investigation is separate. RC2 changes no
projection, Wi-Fi, NEMESIS, Maps/HUD or display-switching code. No causal link
between that display problem and Auto Seat has been established.

## Log retention

NEMESIS service output and Auto Seat diagnostics survive head-unit shutdowns.
Auto Seat diagnostics append only when enabled and rotate at roughly 256 KiB
at startup to `diag.log.1`. Logcat itself is a separate live buffer, not the
persistent Auto Seat history. Raw owner logs are excluded from the public repo
and downloadable source; only this minimal evidence summary is included.

This post was prepared and posted with ChatGPT.
