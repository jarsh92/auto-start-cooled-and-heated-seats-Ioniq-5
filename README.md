# Auto Seat 2.0

> PR #2 prepares the new NEMESIS ID `auto-seat`. The original released APK is unchanged, but migration packaging is not yet vehicle-validated. Existing `coldstart.heat` owners must follow [VEHICLE-TEST.md](VEHICLE-TEST.md) after approval. Same-ID update instructions below describe the original released package only. See [STORE-MIGRATION.md](STORE-MIGRATION.md) and [STORE-SUBMISSION.md](STORE-SUBMISSION.md).

Temperature-based startup heating and ventilation for a NEMESIS-equipped Hyundai Ioniq 5 Gen5W head unit. **2.0 is released following the owner's successful in-car report on the intended US-market vehicle. Other cars and firmware remain unverified.** The launcher label is simply **Auto Seat**.

<img src="artwork/auto-seat-blue-frame.png" alt="Auto Seat Blue Frame icon" width="128">

## Credit

Auto Seat builds on **[HKMC Cold-start Heat](https://github.com/eclipseempire/hkmc-coldstart-heat)** by **Gregory Taylor (eclipseempire)**, originally based on commit `82f86f11eee50a92329be96760770362668f6d18`. His original work provided automatic heated-seat and steering-wheel control; Auto Seat extends that foundation with ventilated-seat controls for an equipped trim, additional startup handling, and a redesigned interface. Thank you for sharing the original work and extension guidance.

It runs on **[NEMESIS](https://github.com/xwtk/hmg_nemesis)** by Gor Mirzoyan (xwtk). The original detection pattern credits [dibble9012/hkmc-carplay-auto-display](https://github.com/dibble9012/hkmc-carplay-auto-display). See [LICENSE](LICENSE) for Gregory Taylor's retained MIT copyright and license, and [UPSTREAM-README.md](UPSTREAM-README.md) for the upstream documentation. NEMESIS is a separate dependency with its own license and is not bundled here.

## What's new in 2.0

- Centered rounded graphite panel, capped at 600 dp and constrained to the available screen width, instead of full-screen stretched controls. Physical width must be checked on the head unit; the design target is approximately 5.5–6 inches.
- Graphite + Ford Blue palette, warm white text, rounded controls, blue navigation/ventilation, and Classic heater red (`#C62828`) for active heating controls.
- Matching driver/passenger columns on both pages, consistent On / Off labels, and individual Apply buttons for both heating and ventilation.
- Matching **Blue Frame** launcher/header icon: white seat outline on graphite with a blue inset border.
- Heating, Ventilation, and Settings tabs, explicit Close, and persistent All off retained.
- Approved balanced UI build (Android internal code 13): fixed-height spacers prevent controls being pushed below the window. Version and launcher label remain 2.0 and Auto Seat, respectively.
- Startup service, build guard, and post-install defaults remain unchanged. The command helper adds isolated single-seat heating actions using the existing verified enum mapping, locks, and manual-priority handling.

## Compatibility — US market only

**This Auto Seat 2.0 package targets Josh's US-market 2023 Hyundai Ioniq 5 with an Android-based Gen5W head unit and NEMESIS already installed. It is not a general installer for every Ioniq 5. The owner reported that the installed 2.0 build works and looks great on this car on November 13, 2026.**

| Vehicle / region / software | Status for this package |
| --- | --- |
| US-market 2023 Ioniq 5, Gen5W, inspected build `eng.vmadmin.20260903.161833` | Owner-reported working on the target car, November 13, 2026. |
| Another US-market Ioniq 5 with the same exact internal build | Unverified. Matching the build is necessary for installation, but does not establish compatibility with its trim or equipment. |
| Other US Ioniq 5 model years, trims, or software builds | Not validated. The installer refuses a different internal build. Do not assume compatibility from the Ioniq 5 name alone. |
| EU / European-market Ioniq 5 | **Not supported by this package. US firmware work does not validate EU firmware.** |
| Canadian or other non-US-market Ioniq 5 | Not supported by this package. |
| Ioniq 5 with ccNC or another head-unit platform | Not supported by this Gen5W package. |
| Other Hyundai, Kia, or Genesis models | Not supported by this package; the original upstream project's broader description is not a compatibility promise for Auto Seat. |

### Required software and equipment

- **Region: US (United States), not EU.** The dashboard temperature unit (°F or °C) is a separate setting; changing it does not make EU firmware compatible.
- **Head unit: Android-based Gen5W**, commonly identified by `S5W_M` in its software information; not ccNC.
- **NEMESIS must already be installed and functioning.** This ZIP does not install NEMESIS or update Hyundai firmware.
- **Exact internal Android build required:** `ro.build.version.incremental=eng.vmadmin.20260903.161833`. This is an internal build identifier, not a substitute for the full region-specific Hyundai software/version string shown in the settings screen.
- The original inspected framework build is dated September 3, 2026. A date alone, or a similar-looking software version, is not sufficient to establish compatibility.
- Heating, ventilated seats, and heated steering-wheel controls require the corresponding hardware to be fitted. Auto Seat does not add ventilation or heating hardware to trims that lack it. Leave unsupported features Off; additional trims still require validation.

### Checking another car

1. Open the head unit's software/version information screen and record the complete software version, model information, vehicle model year, trim, and market region. A photo of that screen is useful when requesting compatibility review.
2. Confirm the unit is Gen5W and NEMESIS is already working. Do not install this package merely because the car is called an Ioniq 5.
3. The installer checks the internal Android build and refuses a mismatch. It does **not** independently validate market region, model year, trim, equipment, or every framework file. Passing the guard is not a guarantee for another car.
4. If it reports an unsupported build, stop and keep the message for review. Do not remove the build guard or change firmware to force installation.

This is an unofficial community project, not affiliated with Hyundai. Compatibility testing on other cars is welcome, but support should be documented only after verifying their region, firmware, equipment, and behavior.

### Existing-app update compatibility

The Android ID `com.nemesis.coldstart`, NEMESIS ID `coldstart.heat`, existing state directory, and synchronization paths are retained for update compatibility. Renaming those identifiers would risk duplicate startup services or losing access to existing settings. Source, APK, service filename, and release filenames use Auto Seat.

## Download and install

Use the supplied **Ioniq5-auto-seat-2.0-USB.zip**. It contains the app package, matching installation descriptor, compatibility guide, and source. Download the [2.0 USB installer](downloads/Ioniq5-auto-seat-2.0-USB.zip?raw=true) and check its [SHA-256 checksum](downloads/SHA256SUMS.txt).

1. Confirm your car matches the compatibility section above. Park the car. Remove old `NEMESIS.sh` and `NEMESIS.data` from the USB root.
2. Extract the **outer USB ZIP** to the USB root. `NEMESIS.data` and `Ioniq5-auto-seat-2.0.zip` must be directly at the root. Leave the inner ZIP compressed.
3. Do not copy the outer folder itself onto the drive: the files must be at the USB root, not one folder deeper. Eject the drive safely from the computer.
4. Insert the USB and approve the NEMESIS update. Wait for completion. **Do not uninstall the existing app first.**
5. Open Auto Seat and verify the icon, centered panel, matching Heating/Ventilation layouts, consistent On / Off wording, saved values, Save startup settings, Back, and Close.
6. On Heating, select a driver level and press Apply driver heating. Check the factory indicator and warmth. Repeat for the passenger. Each individual Apply changes only that seat and leaves the other seat and steering wheel unchanged.
7. Check the corresponding ventilation Apply buttons and physical airflow. Selecting Off changes the individual Apply label to Turn [driver/passenger] seat Off; pressing that button stops either heat or ventilation on that seat. Changing the level alone sends no command.
8. Test Test heating now, Test ventilation now, and All Off while parked. Verify the factory indicators and physical seat response; a successful command response alone does not confirm physical actuation.

Individual Apply commands and tests apply the displayed selections immediately, ignore thresholds, and do not save settings. Off selections skip that seat during mode tests/startup. All off stops both front seats and the steering-wheel heater. Save stores preferences without immediately applying them. Startup runs once per head-unit start, not continuously; manual commands take priority until the next head-unit reboot.

Android may reject a downgrade. If rollback is needed, use a correctly signed higher-version rollback build rather than uninstalling to force a downgrade.

## Build

Requires a JDK with `java com.sun.tools.javac.Main`, Android platform 30, and Android build-tools **30.0.3** (including legacy `dx`, required for DEX 035 / Android 4.4 compatibility).

Set `ANDROID_SDK`, `SIGNING_KEY`, `KEY_ALIAS`, `SIGNING_STORE_PASSWORD`, and `SIGNING_KEY_PASSWORD` privately in your environment. The original private key is **not** included. The build script verifies the installed-app certificate fingerprint and refuses a mismatched key. No replacement key is generated automatically.

```sh
bash tools/build_apk.sh
python3 tests/check_commands.py
python3 tests/check_startup_priority.py
bash tools/make_package.sh
```

`tools/make_package.sh` copies the signed APK, builds the inner NEMESIS package, creates a public source archive, and produces the USB bundle under `dist/`.

## Validation and release status

See [VALIDATION-2.0.md](VALIDATION-2.0.md). The owner reports that this build works and looks great on the intended head unit. The supplied photos show Heating, Ventilation, and Settings on the car; detailed per-feature and long-term reliability results are not independently documented. Please report the model, trim, firmware, and observed behavior with any issue, without uploading private vehicle identifiers or signing material.
