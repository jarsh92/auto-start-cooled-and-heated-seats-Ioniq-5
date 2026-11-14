# Auto Seat 2.0 validation

## Completed off-car

- Compiled against Android platform 30, min/target API 19, using Android build-tools 30.0.3 and legacy dx.
- Compiled DEX header is `dex\n035\0` for the KitKat head unit.
- APK signature verification passes, including v1 (required by KitKat) and v2.
- Signing certificate SHA-256 matches the installed personal build: `6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59`.
- ZIP alignment check passes.
- Manifest: versionName `2.0`, versionCode `13`, application/activity launcher labels `Auto Seat`.
- Command regression passes: 48 original combinations plus 8 isolated single-seat heating levels, short requests, save/read, logging, shared lock, error cleanup, Off, invalid settings.
- Startup/manual-priority regression passes: delayed startup cannot override manual heat; saving works without mv; normal startup ventilates.
- Startup service, build guard, and post-install script remain byte-identical to 1.7.2.
- The command helper adds driver_heat and passenger_heat. Each accepts 0..3, maps Off to enum 2 and heat levels to 6/7/8, and retains shared locks/manual-priority handling. Regression tests verify no extra seat or steering-wheel command is sent and invalid levels are rejected.
- Android layout tests also exercise level selection, isolated Apply heating, ventilation Apply, Off labels/commands, and tab navigation without sending vehicle commands.
- USB descriptor, inner package, embedded APK, source archive, and secret-exclusion checks pass.

## Owner's in-car report

On November 13, 2026, Josh Waldmire reported: “It works and looks great.” The supplied photos show the installed Heating, Ventilation and Settings screens on the target US-market Ioniq 5. This is an owner-reported success on one vehicle; the photos alone do not prove every actuator, startup cycle, threshold, or long-term behavior. No additional vehicle/firmware compatibility is claimed.

Android 4.4 Robolectric tests measured the real MainActivity layout at 1280×620, 1280×480 and 1920×640, checked navigation/footer bounds and body space, and exercised individual Apply/Off and tab interactions without commanding a vehicle. These checks passed before the tested APK was delivered.

## Recommended checks for subsequent installs

1. Confirm installation updates the existing app; launcher label is Auto Seat with the Blue Frame icon.
2. Check the panel is centered and comfortable (design target 5.5–6 inches; not physically calibrated).
3. Open Heating, Ventilation, and Settings; check all controls are reachable by scrolling with no clipping or overlap.
4. Confirm previous settings loaded; adjust a value, Save, close, reopen, and confirm persistence.
5. Test individual Apply driver/passenger heating and ventilation separately while parked. Confirm the other seat and steering wheel are unchanged. Check factory indicators and warmth/airflow. Cycle a seat to Off and press its individual Off button. Selection changes alone must not actuate a seat.
6. Test All off, Back, and Close.
7. Check startup operation and manual priority over a delayed startup action.

## Publication status

The owner explicitly authorized public GitHub publication after reporting the in-car result. The published app binary is the same signed Android version 2.0 / internal code 13 tested by the owner. Publication updates documentation and packaging metadata only; it does not rebuild the APK.
