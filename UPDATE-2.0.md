# Auto Seat 2.0 — Graphite + Ford Blue release

New centered rounded panel (maximum 600 dp), rounded blue/graphite controls, selected tab feedback, and the approved Blue Frame seat icon. App and launcher label: Auto Seat. Android versionName: 2.0; versionCode: 13.

Heating, ventilation, configuration, manual-priority behavior, timeout handling, service IDs, and existing settings paths are preserved from 1.7.2. Startup/install-guard scripts are byte-identical to 1.7.2. The final command helper adds isolated single-seat heating actions.

The release retains Gregory Taylor's MIT license and credits his HKMC Cold-start Heat project, NEMESIS, and the original detection-pattern source.

Prerelease: verify physical panel width, touch layout, saved settings, controls, Back/Close, and actual startup behavior on the head unit before marking stable. The 5.5–6 inch width is a visual target, not a calibrated physical measurement.

Documentation revision: explicitly identifies US-market 2023 Ioniq 5 / Gen5W and exact internal build, excludes EU and other unvalidated platforms/regions, distinguishes internal build from Hyundai software label, and adds first-time USB instructions. APK and production vehicle scripts unchanged.

Layout correction (still version 2.0): fixed unbounded spacer measurement that hid the tabs and controls. Internal Android versionCode increased to 12 for an in-place update; launcher label remains Auto Seat. Original failure reproduced with an Android 4.4 layout test and corrected before rebuilding.

Approved balanced UI build (still version 2.0; internal code 13): Classic heater red #C62828, Ford Blue ventilation/navigation, consistent On / Off wording, matching driver/passenger columns, and individual Apply heating buttons. Individual heating commands use the existing helper path and locks, target one seat, and explicitly support Off. The automatic ventilation switch/threshold behavior is retained. The owner subsequently reported that the build works and looks great, and authorized publication.

Release status: owner-reported working on the intended US-market car on November 13, 2026. Public publication authorized. Broader compatibility and long-term reliability remain unverified. APK unchanged from the tested internal build 13.
