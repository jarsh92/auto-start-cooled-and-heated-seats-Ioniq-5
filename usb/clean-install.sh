#!/system/bin/sh
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
export LD_LIBRARY_PATH=/vendor/lib:/system/lib
umask 077
NEM=/system/xbin/nemesis
die() { echo "STOP: $*"; exit 1; }
require_root() {
    echo 'Identity reported by the Android toolbox:'
    id 2>&1 || echo 'id command unavailable; using kernel process credentials'
    found=0
    if [ -r "/proc/$$/status" ]; then
        while read -r key real effective saved filesystem rest; do
            [ "$key" = 'Uid:' ] || continue
            found=1
            echo "Kernel process UIDs: real=$real effective=$effective saved=$saved filesystem=$filesystem"
            [ "$real" = 0 ] && [ "$effective" = 0 ] && [ "$saved" = 0 ] && [ "$filesystem" = 0 ] || die 'NEMESIS execution is not fully root; no changes made'
            break
        done < "/proc/$$/status"
    fi
    [ "$found" = 1 ] || die 'Cannot verify kernel process credentials; no changes made'
}

echo 'Auto Seat clean installation - autoseat.heat - revision 1'
require_root
[ "$(getprop ro.build.version.incremental)" = eng.vmadmin.20260903.161833 ] || die 'Unsupported firmware'
[ "$(getprop sys.boot_completed)" = 1 ] || die 'Wait for Android to finish starting'
rows=$("$NEM" pkg-list) || die 'Cannot read installed package list'
for id in coldstart.heat auto-seat autoseat.heat; do
    if echo "$rows" | grep -q "^$id|"; then
        die "Package $id is still installed. Use NEMESIS My Packages to uninstall the old Auto Seat before this clean install. No changes made."
    fi
done
[ ! -e /data/nemesis/apps/coldstart.heat ] && [ ! -L /data/nemesis/apps/coldstart.heat ] || die 'Old helper path remains. Do not delete it manually; return this log'
[ ! -e /data/nemesis/apps/autoseat.heat ] && [ ! -L /data/nemesis/apps/autoseat.heat ] || die 'Unregistered new package directory exists; return this log'
install_package() ( umask 022; "$NEM" install ./autoseat.heat-2.0.zip; )
if ! install_package; then
    echo 'INSTALLATION STOPPED. Return this log; do not retry or manually remove files.'
    if [ -x /system/bin/logcat ]; then /system/bin/logcat -d -v time > ./Auto-Seat-Clean-Install-Android.log 2>&1; fi
    exit 1
fi
rows=$("$NEM" pkg-list) || die 'Installed-package query failed after install'
echo "$rows" | grep -q '^autoseat.heat|' || die 'New package not registered after install'
for id in coldstart.heat auto-seat; do
    if echo "$rows" | grep -q "^$id|"; then die 'Conflicting package remains'; fi
done
services=$("$NEM" service list) || die 'Cannot verify service registration'
count=0
while IFS='|' read -r name mode status pid; do
    case "$name" in
        autoseat.heat/*|coldstart.heat/*|auto-seat/*)
            [ "$name" = autoseat.heat/apply ] && [ "$mode" = background ] || die "Unexpected seat service $name"
            count=$((count+1));;
    esac
done <<EOF
$services
EOF
[ "$count" = 1 ] || die 'Expected one Auto Seat service'
path=$(pm path com.nemesis.coldstart) || die 'Android app query failed'
case "$path" in package:/*) path=${path#package:};; *) die 'Installed Android APK path unavailable';; esac
cmp "$path" /data/nemesis/apps/autoseat.heat/app/auto-seat.apk >/dev/null 2>&1 || die 'Installed APK bytes do not match package'
cmp /data/nemesis/apps/coldstart.heat/scripts/seat-action.sh /data/nemesis/apps/autoseat.heat/scripts/seat-action.sh >/dev/null 2>&1 || die 'App helper link files differ'
[ "$(cat /data/nemesis/apps/coldstart.heat/autoseat.heat.bridge)" = autoseat.heat-bridge-v1 ] || die 'App helper ownership marker missing'
echo 'CLEAN INSTALL VERIFIED: Auto Seat registered as autoseat.heat, original APK and one service.'
echo 'The original APK keeps its internal Android name. The compatibility helper is not a second registered package.'
echo 'Settings may remain from the previous installation; review or reset them in Auto Seat as desired.'
echo 'No migration HOLD is used by this package. Startup controls operate according to your settings.'
echo 'Return Auto-Seat-Clean-Install.log before further changes.'
