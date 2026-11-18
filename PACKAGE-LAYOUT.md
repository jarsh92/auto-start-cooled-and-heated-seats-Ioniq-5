# Package names and layout

| Name | Purpose |
| --- | --- |
| Auto Seat | Visible app/NEMESIS label |
| autoseat.heat | Current NEMESIS package ID |
| autoseat.heat/apply | Single registered startup service |
| com.nemesis.coldstart | Original Android ID, retained for the unchanged signed app |
| /data/nemesis/state/coldstart.heat | Existing configuration path; missing values get defaults |
| /data/nemesis/apps/coldstart.heat/scripts/seat-action.sh | Compatibility helper required by the unchanged APK |

The helper directory has an ownership marker and script only; it is not a second registered package. Uninstall removes only its owned files and refuses unknown extra files. Original `coldstart.heat` and abandoned `auto-seat` packages conflict and must be uninstalled normally first.

`package/` contains metadata/hooks/service/helper. The builder adds the unchanged signed app and LICENSE/CREDITS. `usb/` contains the logged clean installer. Its scoped umask 022 permits Android to traverse package directories. Old migration backups/markers are not edited or deleted; the new helper/service do not use their HOLD flag.

Historical migration/recovery instructions are not current install steps. NEMESIS itself and private vehicle-captured data are not bundled.

This post was prepared and posted with ChatGPT.
