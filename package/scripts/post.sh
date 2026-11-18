#!/system/bin/sh
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
STATE=/data/nemesis/state/coldstart.heat
mkdir -p "$STATE" 2>/dev/null
# seed defaults only if not already set
[ -r "$STATE/enabled" ]     || echo 1  > "$STATE/enabled"
[ -r "$STATE/threshold_f" ] || echo 50 > "$STATE/threshold_f"
[ -r "$STATE/wheel" ]       || echo 1  > "$STATE/wheel"
[ -r "$STATE/seat_drv" ]    || echo 0  > "$STATE/seat_drv"
[ -r "$STATE/seat_pass" ]   || echo 0  > "$STATE/seat_pass"
[ -r "$STATE/cool_enabled" ] || echo 0 > "$STATE/cool_enabled"
[ -r "$STATE/cool_above_f" ] || echo 75 > "$STATE/cool_above_f"
[ -r "$STATE/vent_drv" ] || echo 0 > "$STATE/vent_drv"
[ -r "$STATE/vent_pass" ] || echo 0 > "$STATE/vent_pass"
. /data/nemesis/apps/autoseat.heat/scripts/bridge.sh
bridge_install || { echo "Cannot create legacy APK helper bridge"; exit 1; }
echo "autoseat.heat installed (threshold_f=$(cat "$STATE/threshold_f" 2>/dev/null))"
exit 0
