# Auto Seat 2.0 validation — AI-written changes

No independent human code review has been completed. Josh directed the AI development and performed owner vehicle testing; he is not claiming programmer review.

## Current clean release: autoseat.heat

On November 17, 2026 the USB installer returned CLEAN INSTALL VERIFIED and exit 0 on the intended US 2023 IONIQ 5 Limited, Gen5W, build `eng.vmadmin.20260903.161833`, NEMESIS 1.16.7. It verified new package registration, no conflicting old package, original APK bytes, one `autoseat.heat/apply` service and the owned helper. Josh subsequently reported everything worked in the car and no current issue needed attention after being asked to check restart/startup and parked heat/ventilation/Off/wheel behavior. This is an owner report; no independent per-control instrumented report, broad compatibility study or long-term test is claimed.

The release APK is byte-identical to the originally signed 2.0 app. The source/runtime hash inventory pins the owner-tested clean package and USB scripts. Documentation and attribution changes do not alter that runtime. No new app compilation, key generation or signing is used for this release.

Local host checks covered shell syntax; firmware/old-helper guards; fresh defaults and exact helper creation with old migration HOLD present; read/save, isolated heating/ventilation, Off and bad input; disabled startup and warm startup ventilation with old HOLD present; owned helper removal/unknown-file refusal; installer conflict guards; wrapper logging/exit status; and nested archives/unchanged APK. Android and NEMESIS commands were simulated and did not contact the car.

CI additionally runs the command-generation regression, delayed startup/manual-priority regression, portable clean lifecycle tests, actual POSIX host permission-mask checks, deterministic archive/runtime identity tests and the original APK's expected certificate/v1 signature/DEX verification. Source compilation remains separate from distributing the original signed app.

## Limits and historical failures

The abandoned `auto-seat` transaction migration was not the successful installation route. An initial APK install failed; a permission-mask correction allowed original app reinstall, but a later settings restore failed. A read-only vehicle check then verified the original package and all 11 saved settings. The final successful route was owner-requested normal uninstall followed by clean `autoseat.heat` installation, without settings migration/HOLD. Do not use historical migration/recovery bundles as release installers.

Host tests do not reproduce the exact Android framework, physical seat actuators or installed NEMESIS binary. The inherited private umask was a likely install-failure mechanism based on code inspection; an instrumented on-unit root-cause proof was not collected. Exact-state migration is not promised, and interrupted firmware/core/storage recovery is outside this package's scope. Other trims/models/markets, IONIQ 6 and automatic equipment detection remain unverified. Private vehicle logs and settings are deliberately excluded from public source/assets.

This post was prepared and posted with ChatGPT.
