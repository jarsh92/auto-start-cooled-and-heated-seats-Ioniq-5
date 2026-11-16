#!/system/bin/sh
# No command in this file is run against a vehicle by CI.
# USB cwd is the bundle root; actions require a separately approved command.
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
export LD_LIBRARY_PATH=/vendor/lib:/system/lib
umask 077
NEM=/system/xbin/nemesis
BASE=/data/nemesis
STATE=$BASE/state/coldstart.heat
OLD=$BASE/apps/coldstart.heat
NEW=$BASE/apps/auto-seat
BACK=$BASE/backup/auto-seat-migration-v1
LOCK=/dev/seat-comfort/actuation.lock
BUNDLE=$(pwd)
die() { echo "STOP: $*" >&2; exit 1; }
# Recursion uses subshell scope, and rejects links and non-regular nodes.
plain_tree() (
    [ -d "$1" ] && [ ! -L "$1" ] || exit 1
    for f in "$1"/* "$1"/.[!.]* "$1"/..?*; do
        [ -e "$f" ] || [ -L "$f" ] || continue
        [ ! -L "$f" ] || exit 1
        if [ -d "$f" ]; then plain_tree "$f" || exit 1
        else [ -f "$f" ] || exit 1; fi
    done
)
same_tree() (
    plain_tree "$1" && plain_tree "$2" || exit 1
    for f in "$1"/* "$1"/.[!.]* "$1"/..?*; do
        [ -e "$f" ] || continue
        n=${f##*/}
        if [ -d "$f" ]; then same_tree "$f" "$2/$n" || exit 1
        else [ -f "$2/$n" ] && cmp "$f" "$2/$n" >/dev/null 2>&1 || exit 1; fi
    done
    for f in "$2"/* "$2"/.[!.]* "$2"/..?*; do
        [ -e "$f" ] || continue
        n=${f##*/}
        [ -e "$1/$n" ] || exit 1
    done
)
copy_tree() (
    plain_tree "$1" || exit 1
    [ ! -e "$2" ] && [ ! -L "$2" ] || exit 1
    mkdir "$2" || exit 1
    for f in "$1"/* "$1"/.[!.]* "$1"/..?*; do
        [ -e "$f" ] || continue
        n=${f##*/}
        if [ -d "$f" ]; then copy_tree "$f" "$2/$n" || exit 1
        else cp "$f" "$2/$n" || exit 1; fi
    done
    same_tree "$1" "$2"
)
packages() { "$NEM" pkg-list; }
has_package() { packages | grep -q "^$1|"; }
check_services() {
    rows=$("$NEM" service list) || die "Cannot list services"
    count=0
    while IFS='|' read -r q mode status pid; do
        case "$q" in
            coldstart.heat/*|auto-seat/*)
                [ "$q" = "$1/apply" ] && [ "$mode" = background ] || die "Unexpected seat service: $q"
                count=$((count + 1))
                ;;
        esac
    done <<EOF
$rows
EOF
    [ "$count" = 1 ] || die "Expected exactly one seat service"
}
check_apk() {
    path=$(pm path com.nemesis.coldstart) || die "Cannot query installed APK"
    case "$path" in package:/*) path=${path#package:};; *) die "Unexpected APK path";; esac
    [ -f "$path" ] && [ ! -L "$path" ] || die "APK missing or linked"
    cmp "$path" "$BUNDLE/original/app/auto-seat.apk" >/dev/null 2>&1 || die "Installed APK differs from original signed 2.0"
}
check_environment() {
    [ "$(id -u)" = 0 ] || die "Run through NEMESIS as root"
    [ "$(getprop ro.build.version.incremental)" = eng.vmadmin.20260903.161833 ] || die "Unsupported firmware"
    [ "$(getprop sys.boot_completed)" = 1 ] || die "Android must be fully started"
    for tool in cmp cp mkdir rmdir rm cat grep sync am pm; do
        command -v "$tool" >/dev/null 2>&1 || die "Missing required toolbox command: $tool"
    done
    [ -x "$NEM" ] || die "NEMESIS missing"
    plain_tree "$BUNDLE/original" || die "Missing or unsafe original package tree"
    [ -r "$BUNDLE/original.zip" ] && [ -r "$BUNDLE/candidate.zip" ] || die "Missing recovery or candidate ZIP"
    "$NEM" pkg-info "$BUNDLE/original.zip" | grep -q '^id=coldstart.heat$' || die "Invalid recovery package"
    "$NEM" pkg-info "$BUNDLE/candidate.zip" | grep -q '^id=auto-seat$' || die "Invalid candidate"
}
check_old() {
    has_package coldstart.heat || die "Old package is not registered"
    ! has_package auto-seat || die "Both package IDs are registered"
    same_tree "$OLD" "$BUNDLE/original" || die "Legacy files differ; unsupported old version or uninstall hooks"
    check_services coldstart.heat
    check_apk
    plain_tree "$STATE" || die "State is missing, linked, or has special files"
}
take_lock() {
    mkdir -p /dev/seat-comfort || die "Cannot create lock parent"
    mkdir "$LOCK" 2>/dev/null || die "Seat command active or interrupted lock; do not force-clear"
    trap 'rmdir "$LOCK" 2>/dev/null' EXIT
    trap 'exit 1' HUP INT TERM
    echo migration > /dev/seat-comfort/manual.override || die "Cannot suppress delayed startup"
}
snapshot_ok() {
    [ -f "$BACK/READY" ] || die "No complete snapshot; do not uninstall anything"
    same_tree "$BACK/state" "$BACK/state-check" || die "Snapshot copies disagree"
    cmp "$BACK/original.zip" "$BUNDLE/original.zip" >/dev/null 2>&1 || die "Recovery archive differs from snapshot"
}
restore_state() {
    snapshot_ok
    # Only this fixed application state directory is replaced.
    if [ -e "$STATE" ] || [ -L "$STATE" ]; then
        plain_tree "$STATE" || die "Live state unsafe"
        rm -r "$STATE" || die "Cannot replace state"
    fi
    copy_tree "$BACK/state" "$STATE" || die "State restore failed; hold retained"
    sync || die "Cannot sync restored state"
    same_tree "$BACK/state" "$STATE" || die "Restored state does not match"
}
verify_new() {
    has_package auto-seat && ! has_package coldstart.heat || die "Package registration mismatch"
    check_services auto-seat
    check_apk
    same_tree "$NEW" "$BUNDLE/candidate" || die "Installed new files differ"
    cmp "$OLD/scripts/seat-action.sh" "$NEW/scripts/seat-action.sh" >/dev/null 2>&1 || die "Legacy helper bridge differs"
    [ "$(cat "$OLD/auto-seat.bridge")" = auto-seat-bridge-v1 ] || die "Missing bridge marker"
    [ ! -e "$OLD/NEMESIS.data" ] || die "Legacy package tree still present"
    same_tree "$BACK/state" "$STATE" || die "Settings changed during migration"
}
action=${1:-check}
case "$action" in
    check|migrate|recover|accept) ;;
    *) die "Usage: migrate.sh check|migrate|recover|accept [explicit-token]";;
esac
check_environment
case "$action" in
check)
    check_old
    [ ! -e "$BACK" ] && [ ! -L "$BACK" ] || die "Prior migration snapshot exists; inspect it first"
    echo "PREFLIGHT PASS: supported original 2.0, APK, state and service; no installation changes made."
    ;;
migrate)
    [ "${2:-}" = APPROVE-MIGRATION ] || die "Explicit APPROVE-MIGRATION token required"
    check_old
    [ ! -e "$BACK" ] && [ ! -L "$BACK" ] || die "Never overwrite an existing snapshot"
    take_lock
    "$NEM" service stop coldstart.heat/apply || die "Cannot stop old service"
    am force-stop com.nemesis.coldstart || die "Cannot close app"
    mkdir -p "$BASE/backup" || die "Cannot create backup parent"
    mkdir "$BACK" || die "Cannot create transaction"
    echo hold > "$BACK/HOLD" || die "Cannot create persistent hold"
    copy_tree "$STATE" "$BACK/state" || die "Snapshot failed; old package still installed"
    copy_tree "$STATE" "$BACK/state-check" || die "Snapshot verification copy failed"
    cp "$BUNDLE/original.zip" "$BACK/original.zip" || die "Cannot save recovery package"
    cmp "$BUNDLE/original.zip" "$BACK/original.zip" || die "Recovery copy failed"
    same_tree "$STATE" "$BACK/state" && same_tree "$BACK/state" "$BACK/state-check" || die "Snapshot changed"
    sync || die "Snapshot sync failed"
    echo ready > "$BACK/READY" || die "Cannot mark complete snapshot"
    sync || die "Ready marker sync failed"
    snapshot_ok
    # Only supported package manager operations; no --force, registry edit, or key.
    "$NEM" uninstall coldstart.heat || die "Uninstall failed; use recovery and keep logs"
    ! has_package coldstart.heat || die "Old registration remains"
    restore_state
    "$NEM" install "$BUNDLE/candidate.zip" || die "New install failed; use recovery"
    verify_new
    echo migrated > "$BACK/MIGRATED" || die "Cannot mark migration"
    sync || die "Cannot sync completion"
    echo "MIGRATION VERIFIED OFFLINE ON THIS UNIT. HOLD retained. Compare UI settings, then request acceptance."
    ;;
recover)
    [ "${2:-}" = APPROVE-RECOVERY ] || die "Explicit APPROVE-RECOVERY token required"
    snapshot_ok
    take_lock
    echo hold > "$BACK/HOLD" || die "Cannot hold new service"
    sync || die "Cannot sync hold"
    am force-stop com.nemesis.coldstart || die "Cannot close app"
    if has_package auto-seat; then
        "$NEM" service stop auto-seat/apply || die "Cannot stop new service"
        "$NEM" uninstall auto-seat || die "Cannot uninstall new package; never force"
    fi
    if has_package coldstart.heat; then
        "$NEM" service stop coldstart.heat/apply || die "Cannot stop original before restore"
    fi
    restore_state
    if has_package coldstart.heat; then
        same_tree "$OLD" "$BUNDLE/original" || die "Old package differs; manual review required"
    else
        # Never remove an orphan or damaged bridge recursively.
        [ ! -e "$OLD" ] && [ ! -L "$OLD" ] || die "Orphan legacy path; manual review required"
        "$NEM" install "$BACK/original.zip" || die "Original reinstall failed; snapshot retained"
    fi
    # The original postinstall seeds absent defaults; restore the exact snapshot
    # again while the actuation lock/manual marker still suppress startup.
    restore_state
    check_old
    same_tree "$STATE" "$BACK/state" || die "Recovered settings mismatch"
    echo recovered > "$BACK/RECOVERED" || die "Cannot record recovery"
    rm "$BACK/HOLD" || die "Cannot clear hold"
    sync || die "Cannot sync recovery"
    echo "RECOVERY VERIFIED: original 2.0 and settings restored. No actuator commands sent; reboot only after approval."
    ;;
accept)
    [ "${2:-}" = APPROVE-ACCEPTANCE ] || die "Explicit APPROVE-ACCEPTANCE token required"
    snapshot_ok
    [ -f "$BACK/MIGRATED" ] && [ -f "$BACK/HOLD" ] && [ ! -e "$BACK/RECOVERED" ] || die "Not awaiting acceptance"
    verify_new
    rm "$BACK/HOLD" || die "Cannot clear hold"
    sync || die "Cannot sync acceptance"
    echo "Acceptance recorded. No service started. Startup acts only on a later approved reboot."
    ;;
esac
