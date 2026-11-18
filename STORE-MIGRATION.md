# Retired transaction migration — use clean installation

**AI-written changes · No independent human code review.** The unsuccessful `auto-seat` settings-migration/HOLD workflow is retired and is not included in this release. Do not follow historical migration/recovery instructions to install the current package.

The current ID is `autoseat.heat`. Use normal NEMESIS My Packages uninstall of an older Auto Seat, followed by the single clean USB installer in README.md. Existing settings may remain; missing values get defaults. No exact settings migration is promised. The installer does not uninstall automatically or erase old backups.

The unchanged Android app still uses `com.nemesis.coldstart` and its fixed helper path. PACKAGE-LAYOUT.md explains why an owned legacy helper directory exists without registering a second package/service.

This post was prepared and posted with ChatGPT.
