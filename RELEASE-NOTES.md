# Auto Seat 2.0 (autoseat.heat) — AI-written enhancements

**Auto Seat additions were written by OpenAI ChatGPT/Codex under Josh Waldmire's direction. No independent human programmer has reviewed them.** Josh directed the project and tested it on his car; he does not claim to have programmed it. Original HKMC Cold-start Heat authorship remains credited to Gregory Taylor (eclipseempire).

This release uses the final NEMESIS ID **`autoseat.heat`**. The screen name stays **Auto Seat**, with the original signed 2.0 Android app unchanged. Heating, temperature-based ventilation, individual seat controls and the Blue Frame interface are included. It is a clean-install release; the old settings-migration/HOLD workflow is retired.

**Use `Auto-Seat-2.0-autoseat.heat-USB.zip` for vehicle installation.** Extract all contents to an otherwise empty USB. Existing users must first uninstall the old Auto Seat through NEMESIS My Packages, then insert the prepared USB while parked and fully started and approve Execute. The installer does not uninstall automatically. Read the README first. Settings may remain or be reset in the app; no settings migration is promised.

Clean installation was verified on Josh's **US 2023 IONIQ 5 Limited, Gen5W, internal build `eng.vmadmin.20260903.161833`, NEMESIS 1.16.7**. He reports everything works in the car. This is one owner's report; another trim, region, firmware or model is not established as compatible. **IONIQ 6 is not tested or supported by this release.** Do not bypass the guard to try another car.

AI tools are welcome for inspecting, criticizing, forking and adapting the MIT-licensed project with upstream credit/license retained. IONIQ 6 owners and others can open issues with their equipment/software details. We may help investigate, but cannot promise a port. **Any development assistance from this project will be AI-generated with ChatGPT/Codex under Josh's direction, not independent human programming or review.** Validate physical behavior on the actual vehicle.

Planned work: reliable read-only ventilated-seat equipment detection where possible; a manual enable/disable option for trim differences or uncertain detection; UI refinements; and separately validated vehicle adaptations. These are plans, not features in this release or delivery promises.

The builder checks runtime files against the vehicle-tested clean build. CI checks original APK signature/bytes, shell/regression behavior, package layout and release checksums. Simulations and owner testing do not replace independent review. Private vehicle logs, settings and signing material are excluded.

This post was prepared and posted with ChatGPT.
