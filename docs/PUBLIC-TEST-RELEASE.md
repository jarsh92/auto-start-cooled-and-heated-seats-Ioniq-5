# Auto Seat 2.0 — Startup Confirmation and Retry RC2 (Public Test)

**Testing release — feedback welcome.** This fixes a confirmed startup-temperature defect in the previous releases. It is not yet validated across repeated real-world starts or independently reviewed by a human programmer.

## Why this test release exists

Owner logs show the earlier service accepting an unready ECO reading of **−40°C/−40°F** and commanding heating. Josh also reported a recent trip with **73°F on the dashboard but heated seats activated**; that exact trip cannot be conclusively identified in the logs.

RC1 prevented uncorroborated −40° readings from triggering heating, but owner logs then showed missed starts even with valid 47°F/46°F dashboard readings. RC2:

- Confirms the requested **heat / ventilation / no-action** result, allowing temperature changes larger than 1–2 degrees when the action remains the same.
- Retains brief temperature events in a short-lived live capture so polling does not lose them when the Android log buffer rolls over.
- Keeps the invalid-temperature rejection, ready-dashboard preference, real elapsed deadlines and shared control lock.
- Allows one delayed retry at about **3–4 minutes after service entry**, only if the first attempt remained undecided. A successful heat/ventilation or neutral decision exits without further adjustment.
- Requires fresh readings for the retry and leaves seats unchanged after final timeout.

**Manual-control limitation:** Auto Seat's manual controls cancel pending automation. Changes made with the factory seat/wheel buttons are not detected, so a delayed automatic action could change a factory-selected level. Factory manual-input detection needs separate validation. Test this candidate while parked.

This revision changes Auto Seat startup handling only. No Android Auto, Wi-Fi, NEMESIS or Maps/HUD fix is included or claimed.

## Download and install

Use **Auto-Seat-2.0-autoseat.heat-startup-fix-RC2-USB.zip** below. This is a NEW revision of the startup service; RC2 has not yet been tested on the vehicle. The UI and original signed Android APK remain unchanged. App version stays **2.0** and NEMESIS package ID stays **autoseat.heat**.

This uses the existing **clean installer**, not an in-place update:

1. Keep your previous installer for rollback and record your settings.
2. While parked, uninstall the installed Auto Seat through **NEMESIS → My Packages → Auto Seat → Uninstall**.
3. Extract **all contents** of the public-test USB ZIP onto an otherwise empty USB. Keep the inner package ZIP compressed.
4. With Android fully started, insert the USB and approve **Execute**.
5. Review saved settings and test controls while parked. The normal uninstaller retains settings; check them rather than assuming they are correct. Keep the installation log if anything fails.

Do not bypass firmware/helper guards or delete package directories manually. Read the included instructions before installation.

## Evidence and remaining testing

- The original service was reproduced heating on simulated −40°, while the fixed service waits for 73°F and chooses ventilation.
- All 27 startup-temperature test methods and the existing command, lifecycle and manual-priority checks pass.
- Packaging verifies the original APK bytes, signing certificate, KitKat v1 signature and DEX 035. Only the startup service differs from the vehicle-tested runtime.
- RC1 was installed and subsequently showed missed starts in owner logs. **RC2 has host-test evidence only; its initial vehicle test and repeated cold/warm starts are still pending.**
- Fresh readings are still required. If neither the initial attempt nor the bounded retry receives usable data, no automatic action is issued. Manual controls remain available.

Leave diagnostic logging enabled during testing. Report approximate incident time, dashboard temperature, chosen thresholds, expected behavior, actual behavior and exact vehicle/software information. Logs persist without a USB connected. Review logs for private information before sharing them publicly.

## Compatibility

Intended only for the owner's **US-market 2023 Hyundai IONIQ 5 Limited, Gen5W**, internal build **eng.vmadmin.20260903.161833**, with **NEMESIS 1.16.7** as previously tested for the earlier build. The owner is separately updating NEMESIS; this candidate does not install that update and does not claim validation on the newer NEMESIS version. Other cars, trims and firmware remain unverified. **No EU or ccNC support is claimed.** Required seat/wheel equipment must be present.

## Credit and development disclosure

Based on **HKMC Cold-start Heat by Gregory Taylor (eclipseempire)**, with its MIT license and original copyright retained. NEMESIS is by **Gor Mirzoyan (xwtk)** and is a separate dependency. No original-author endorsement is implied.

Auto Seat enhancements, this fix and these notes were written by **OpenAI ChatGPT/Codex under Josh Waldmire's direction**. Josh organizes the project and tests the vehicle; no independent human programmer has reviewed these changes.

This post was prepared and posted with ChatGPT.
