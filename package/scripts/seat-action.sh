#!/system/bin/sh
# Short, fixed-argument entry point. Keep shell bodies out of the NEMESIS socket.
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
STATE=/data/nemesis/state/coldstart.heat
LOCKBASE=/dev/seat-comfort
SERVICE=service
umask 077
mkdir -p "$STATE" || exit 1
diag() {
    [ "$(cat "$STATE/diag" 2>/dev/null)" = 1 ] || return 0
    echo "manual $(date 2>/dev/null): $*" >> "$STATE/diag.log"
}
fail() { echo "ERR $*"; diag "ERROR $*"; exit 1; }
level() { case "$1" in 0|1|2|3) ;; *) fail 'invalid seat level';; esac; }
flag() { case "$1" in 0|1) ;; *) fail 'invalid flag';; esac; }
number() { case "$1" in ''|*[!0-9]*) fail 'invalid numeric setting';; esac; }
mode=$1
shift
case "$mode" in
    heat) [ "$#" = 3 ] || fail 'heat argument count'; flag "$1"; level "$2"; level "$3";;
    vent) [ "$#" = 2 ] || fail 'vent argument count'; level "$1"; level "$2";;
    driver|passenger|driver_heat|passenger_heat) [ "$#" = 1 ] || fail 'seat argument count'; level "$1";;
    off) [ "$#" = 0 ] || fail 'off argument count';;
    save)
        [ "$#" = 11 ] || fail 'settings argument count'
        for value in "$@"; do number "$value"; done
        flag "$1"; [ "$2" -le 80 ] || fail 'heating threshold range'
        flag "$3"; level "$4"; level "$5"; flag "$6"; flag "$7"
        [ "$8" -le 120 ] || fail 'ventilation threshold range'
        level "$9"; level "${10}"; flag "${11}"
        if [ "$7" = 1 ] && [ "$8" -le "$2" ]; then fail 'ventilation threshold must exceed heating threshold'; fi
        ;;
    read)
        [ "$#" = 0 ] || fail 'read argument count'
        for key in enabled threshold_f wheel seat_drv seat_pass ui_temp_is_c cool_enabled cool_above_f vent_drv vent_pass diag; do
            value=$(cat "$STATE/$key" 2>/dev/null)
            echo "$key=$value"
        done
        echo CONFIG_READ
        exit 0
        ;;
    *) fail 'unknown action';;
esac
mkdir -p "$LOCKBASE" || fail 'cannot create command lock directory'
LOCK=$LOCKBASE/actuation.lock
mkdir "$LOCK" 2>/dev/null || fail 'another seat command is active'
trap 'rmdir "$LOCK"' EXIT
trap 'exit 1' HUP INT TERM
diag "BEGIN $mode args=$*"
case "$mode" in
    heat|vent|driver|passenger|driver_heat|passenger_heat|off)
        # Prevent a startup temperature wait from later undoing manual intent.
        echo "$mode" > "$LOCKBASE/manual.override" || fail 'could not record manual priority'
        ;;
esac
call() {
    reply=$("$SERVICE" call "$1" "$2" i32 "$3" 2>&1)
    rc=$?
    diag "service=$1 transaction=$2 value=$3 exit=$rc reply=$reply"
    [ "$rc" = 0 ] || { echo "ERR service call: $reply"; return 1; }
    case "$reply" in
        *'Parcel(00000000'*) return 0;;
        *) echo "ERR unexpected service reply: $reply"; return 1;;
    esac
}
seat() { call com.hkmc.micom.usm "$1" "$2"; }
case "$mode" in
    save)
        for key in enabled threshold_f wheel seat_drv seat_pass ui_temp_is_c cool_enabled cool_above_f vent_drv vent_pass diag; do
            # Same simple write used by the original on-car settings app.
            # Do not depend on mv, which is not verified on this head unit.
            echo "$1" > "$STATE/$key" || fail "could not save $key; settings may be partially written"
            shift
        done
        ;;
    heat)
        if [ "$1" = 1 ]; then call com.hkmc.vr 16 1 || exit 1; fi
        if [ "$2" -gt 0 ]; then seat 213 $(($2 + 5)) || exit 1; fi
        if [ "$3" -gt 0 ]; then seat 214 $(($3 + 5)) || exit 1; fi
        ;;
    vent)
        if [ "$1" -gt 0 ]; then seat 213 $(($1 + 2)) || exit 1; fi
        if [ "$2" -gt 0 ]; then seat 214 $(($2 + 2)) || exit 1; fi
        ;;
    driver_heat|passenger_heat)
        if [ "$mode" = driver_heat ]; then transaction=213; else transaction=214; fi
        if [ "$1" = 0 ]; then value=2; else value=$(($1 + 5)); fi
        seat "$transaction" "$value" || exit 1
        ;;
    driver|passenger)
        if [ "$mode" = driver ]; then transaction=213; else transaction=214; fi
        if [ "$1" = 0 ]; then value=2; else value=$(($1 + 2)); fi
        seat "$transaction" "$value" || exit 1
        ;;
    off)
        failed=0
        call com.hkmc.vr 16 0 || failed=1
        seat 213 2 || failed=1
        seat 214 2 || failed=1
        [ "$failed" = 0 ] || exit 1
        ;;
esac
diag "DONE $mode"
echo COMMANDS_ACCEPTED
