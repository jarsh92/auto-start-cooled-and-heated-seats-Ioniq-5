# Auto Seat 2.0 — AI-written enhancements

> **Auto Seat additions were written by OpenAI ChatGPT/Codex under Josh Waldmire's direction. No independent human programmer has reviewed these changes.** Josh is the project organizer and vehicle tester, not the programmer. Original heating-project authorship belongs to Gregory Taylor (eclipseempire), credited below.

Automatic startup heating and ventilation, with individual seat controls, for the tested US-market Hyundai IONIQ 5 Gen5W head unit running NEMESIS. The visible app name is **Auto Seat**; the current NEMESIS package ID is **`autoseat.heat`**.

<img src="artwork/auto-seat-blue-frame.png" alt="Auto Seat Blue Frame icon" width="128">

Josh's main goal was to add temperature-based seat ventilation for equipped vehicles to the original heating-focused project. ChatGPT/Codex wrote the Auto Seat-specific code, interface changes, package scripts, tests and documentation at his direction. Josh supplied requirements, design choices and hands-on vehicle feedback. Automated tests and owner testing are not independent human code review.

## Download and install

**[Download the current Auto Seat USB installer](https://github.com/jarsh92/auto-start-cooled-and-heated-seats-Ioniq-5/releases/download/v2.0-autoseat.heat-r1/Auto-Seat-2.0-autoseat.heat-USB.zip)**

1. Extract **all contents** of this one ZIP directly onto an otherwise empty USB. `NEMESIS.data` and `NEMESIS.sh` must be at the top level. Leave the inner package ZIP compressed.
2. If an older Auto Seat is installed, use **NEMESIS → My Packages → Auto Seat → Uninstall** first. Removing only the Android app icon does not remove its NEMESIS service/package. Existing users of this exact `autoseat.heat` version should not reinstall unnecessarily.
3. While parked with Android fully started and NEMESIS already working, insert the prepared USB and approve **Execute**. The script installs and verifies the expected app, helper and single service. Keep USB and power connected until it finishes.
4. Open Auto Seat, review settings and test controls while parked. Existing settings may remain; missing settings receive defaults. You can reset them in the app. A normal restart lets you check startup behavior under your chosen thresholds.
5. The USB contains **`Auto-Seat-Clean-Install.log`**. If installation stops, keep the files unchanged and return that log before retrying. A failure also saves `Auto-Seat-Clean-Install-Android.log` when Android logcat is available. Logs may contain private information; review/redact them before posting publicly.

The installer does **not** automatically uninstall packages, migrate settings, run a backup-restore transaction or use the retired migration HOLD workflow. Historical `auto-seat` migration/recovery ZIPs are not this release. Old backups are untouched. Use normal NEMESIS operations rather than deleting package directories or bypassing guards.

Normal removal: NEMESIS My Packages → Auto Seat → Uninstall. Its owned helper is removed; settings are retained. No firmware update or NEMESIS installation is included.

## Tested status and compatibility

On November 17, 2026, clean installation succeeded on Josh's **US 2023 IONIQ 5 Limited, Gen5W**, internal build **`eng.vmadmin.20260903.161833`**, with **NEMESIS 1.16.7**. The installer verified registration, original APK bytes, owned helper and one service. Josh subsequently reported everything works in the car and he found nothing needing attention. This is one owner's report, not independent review, a multi-vehicle study or a long-term reliability guarantee.

| Vehicle / platform | Status |
| --- | --- |
| Josh's US 2023 IONIQ 5 Limited, exact build above | Clean installation verified; owner reports working operation |
| Another IONIQ 5, even with the same build | Unverified; region, model year, trim and equipment matter |
| IONIQ 6 | Interest/adaptation welcome; **not tested or supported by this release** |
| Other firmware, non-US markets, ccNC, other Hyundai/Kia/Genesis models | Not validated or supported by this package |

The guard checks the exact internal build, not trim, market or equipment. Passing it does not prove another car is compatible. Heating, ventilation and the heated wheel require the corresponding hardware. **Do not remove the firmware guard or activate controls to discover whether equipment exists.** Ventilation-equipment detection and trim-based enable/disable controls are not yet implemented; an unequipped vehicle needs an independently validated adaptation.

The signed Auto Seat 2.0 APK is reused unchanged. Executable package and USB files are checked against hashes of the vehicle-tested clean build; public credits/instructions can change independently. See [VALIDATION-2.0.md](VALIDATION-2.0.md).

## AI development, reuse and help with other cars

You are welcome to inspect, criticize, fork and adapt the project under its [MIT license](LICENSE), including by using AI tools to take it apart, explain it, find defects or help adapt it to your car. Preserve the original license and attribution. AI suggestions can be wrong; validate changes against the actual firmware, equipment and vehicle behavior before installation.

Josh welcomes issues and contributions, including interest from IONIQ 6 owners. Include model/year/trim/market, head-unit type, complete software version, NEMESIS version and the observed behavior. Do not upload keys or private vehicle data. We can try to investigate and help develop adaptations, but cannot promise compatibility, response time or a working port.

**Development assistance and proposed fixes from this project will be AI-generated with ChatGPT/Codex under Josh's direction, not independently written or reviewed by a human automotive/software engineer.** AI cannot independently validate a physical vehicle. Testing evidence and limits will be documented. Human technical review is welcome, but none has been completed for these Auto Seat changes.

## Planned future work — not included in 2.0

- Read-only detection of ventilated-seat equipment, if a reliable equipment signal is found.
- A remembered manual ventilation enable/disable choice for different trims or uncertain detection, honored by the UI and startup service.
- UI layout, wording and usability refinements.
- Investigation of other vehicles, including IONIQ 6, with separate firmware/equipment validation. These are plans, not compatibility commitments or delivery-date promises.

## Credit

Based on **[HKMC Cold-start Heat](https://github.com/eclipseempire/hkmc-coldstart-heat)** by **Gregory Taylor (eclipseempire)**, upstream base commit `82f86f11eee50a92329be96760770362668f6d18`. His original work focused on startup heated seats and steering-wheel heating. The AI disclosure does not attribute his original code to AI or imply his review/endorsement of the additions.

[NEMESIS](https://github.com/xwtk/hmg_nemesis) is by Gor Mirzoyan (xwtk), separate and not bundled. The original detection pattern credits [dibble9012/hkmc-carplay-auto-display](https://github.com/dibble9012/hkmc-carplay-auto-display). See [CREDITS.md](CREDITS.md).

## Source and package identity

See [BUILDING.md](BUILDING.md). Package `autoseat.heat` registers `autoseat.heat/apply`. The unchanged Android ID is `com.nemesis.coldstart`; its fixed helper path requires an owned helper directory called `coldstart.heat`. That directory is not a second registered package/service. See [PACKAGE-LAYOUT.md](PACKAGE-LAYOUT.md).

This post was prepared and posted with ChatGPT.
