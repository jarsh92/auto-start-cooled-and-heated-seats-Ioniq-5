#!/system/bin/sh
# coldstart.heat - on each start, if outside temp is below threshold_f, apply
# the configured heaters (steering wheel + driver/passenger seats) via the VR
# command channel. Config lives in one-value files written by the UI app.
#
# Verified actuation on-car (NEEV.USA...260507):
#   wheel:      service call com.hkmc.vr 16 i32 1              (on)
#   drv seat:   service call com.hkmc.micom.usm 213 i32 <enum> (setFrontSeatHeatDrvStep)
#   pass seat:  service call com.hkmc.micom.usm 214 i32 <enum> (setFrontSeatHeatAstStep)
#   seat enum:  2=Off 6=Low 7=Med 8=High ; config level 1/2/3 maps to 6/7/8
# Outside temperature comes from a fresh dashboard temp line
# "setOutsideTempUIAdvanced::temp = X / tempunit = Y". tempunit gives BOTH the
# unit and validity: 2=Fahrenheit, 1=Celsius, -1/0=NOT READY (early-boot
# sentinel, temp reads -1.0). ECO JSON "outTemperature" (Celsius) is a fallback,
# but its uncorroborated -40C initialization value must never choose heating.
# A ready dashboard declares its unit; only a missing unit uses ui_temp_is_c.
# Confirm the requested action across polls, not an exact temperature/source.
# A bounded live capture retains records that would leave logcat's ring buffer.
# One delayed retry is allowed only if no startup decision was reached.
#
# Runs once per boot (mode=background). TEST WHILE PARKED.
#
# Optional diagnostics: with diag=1 (default 0), every start also appends a
# timestamped record to diag.log (what temp was read, from which source, and
# the fire/no-fire decision) and copies it to a plugged-in USB stick. Off by
# default and zero-overhead when off; turn it on from the app only to capture
# a log. Read it with: nemesis root -c "cat /data/nemesis/state/coldstart.heat/diag.log"
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
export LD_LIBRARY_PATH=/vendor/lib:/system/lib


TAG=coldstart.heat
STATE=/data/nemesis/state/$TAG
DIAG=$STATE/diag.log
mkdir -p "$STATE" 2>/dev/null
D() { :; }               # diagnostic logger: no-op unless diag=1 (redefined below)
_copy_usb() { :; }       # copy diag.log to a plugged USB: no-op unless diag=1
log() { echo "coldstart: $(date 2>/dev/null) $*"; D "$*"; }

cfg() { _f="$STATE/$1"; _d="$2"; if [ -r "$_f" ]; then read -r _v < "$_f" 2>/dev/null; case "$_v" in ''|*[!0-9-]*) echo "$_d";; *) echo "$_v";; esac; else echo "$_d"; fi; }
# map UI level 1/2/3 (Low/Med/High) -> seat enum 6/7/8 ; anything else -> 2 (off)
seat_enum() { case "$1" in 1) echo 6;; 2) echo 7;; 3) echo 8;; *) echo 2;; esac; }

vent_enum() { case "$1" in 1) echo 3;; 2) echo 4;; 3) echo 5;; *) echo 2;; esac; }
COOL_ENABLED=$(cfg cool_enabled 0)
COOL_ABOVE_F=$(cfg cool_above_f 75)
VENT_DRV=$(cfg vent_drv 0)
VENT_PASS=$(cfg vent_pass 0)
ENABLED=$(cfg enabled 1)
THRESH_F=$(cfg threshold_f 50)
WHEEL=$(cfg wheel 1)          # 0/1
SEAT_DRV=$(cfg seat_drv 0)    # 0..3
SEAT_PASS=$(cfg seat_pass 0)  # 0..3
UI_IS_C=$(cfg ui_temp_is_c 0) # 1 if the dashboard shows Celsius (fallback temp source)
MAX_WAIT=$(cfg max_wait 120)
DIAG_ON=$(cfg diag 0)         # 1 = append a persistent timestamped record to diag.log

# enable persistent diagnostics only when asked
if [ "$DIAG_ON" = "1" ]; then
    _sz=0
    [ ! -r "$DIAG" ] || _sz=$(wc -c < "$DIAG" 2>/dev/null || echo 0)
    case "$_sz" in ''|*[!0-9]*) _sz=0;; esac
    [ "$_sz" -gt 262144 ] && mv "$DIAG" "$DIAG.1" 2>/dev/null   # rotate past ~256 KB
    D() { echo "$*" >> "$DIAG" 2>/dev/null; sync 2>/dev/null; }
    _copy_usb() { for _u in /storage/usb0 /storage/usb1 /mnt/media_rw/usb0 /mnt/usbhost0; do [ -d "$_u" ] && cp "$DIAG" "$_u/coldstart-diag.log" 2>/dev/null && { D "(copied diag.log to $_u)"; return; }; done; }
    D "================================================================"
    D "RUN wall=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null) uptime=$(read -r _up _rest < /proc/uptime; echo "${_up%%.*}")s"
fi

log "start enabled=$ENABLED threshold_f=$THRESH_F wheel=$WHEEL drv=$SEAT_DRV pass=$SEAT_PASS ui_is_c=$UI_IS_C cool_enabled=$COOL_ENABLED cool_above_f=$COOL_ABOVE_F vent_drv=$VENT_DRV vent_pass=$VENT_PASS diag=$DIAG_ON"
if [ "$ENABLED" != "1" ]; then log "disabled; no action"; _copy_usb; exit 0; fi

# Read the kernel clock with shell builtins: wall time changes during boot,
# and this head unit does not reliably provide cut/tail.
clock_seconds() {
    read -r _uptime _unused < /proc/uptime || return 1
    _uptime=${_uptime%%.*}
    case "$_uptime" in ''|*[!0-9]*) return 1;; esac
    echo "$_uptime"
}

# One logcat snapshot per poll, so both sources describe the same buffer.
# Keep complete lines (including logcat timestamps) to distinguish new records.
read_sources() {
    if [ -n "$LISTENER_PID" ] && kill -0 "$LISTENER_PID" 2>/dev/null; then
        _records=$(grep -E '"outTemperature"|setOutsideTempUIAdvanced::temp =' "$CAPTURE" 2>/dev/null)
    else
        _records=$(logcat -d -v time 2>/dev/null | grep -E '"outTemperature"|setOutsideTempUIAdvanced::temp =')
    fi
    ECO_LINE=""; UI_LINE=""
    while IFS= read -r _record; do
        case "$_record" in *'"outTemperature"'*) ECO_LINE=$_record;; esac
        case "$_record" in *'setOutsideTempUIAdvanced::temp ='*) UI_LINE=$_record;; esac
    done <<EOF
$_records
EOF
}

LISTENER_PID=""; CAPTURE_DIR=""; CAPTURE=""; LOCK_HELD=0
cleanup() {
    if [ -n "$LISTENER_PID" ]; then
        kill "$LISTENER_PID" 2>/dev/null
        wait "$LISTENER_PID" 2>/dev/null
    fi
    [ "$LOCK_HELD" != 1 ] || rmdir "$LOCK" 2>/dev/null
    if [ -n "$CAPTURE_DIR" ]; then
        rm -f "$CAPTURE" 2>/dev/null
        rmdir "$CAPTURE_DIR" 2>/dev/null
    fi
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

manual_stop() {
    if [ -f /dev/seat-comfort/manual.override ]; then
        log 'manual command already requested this boot; skipping pending startup action'
        _copy_usb; exit 0
    fi
}

temperature_action() {
    if [ "$1" -lt "$THRESH_F" ]; then ACTION=heat
    elif [ "$COOL_ENABLED" = 1 ] && [ "$1" -gt "$COOL_ABOVE_F" ]; then ACTION=vent
    else ACTION=none; fi
}

new_record() {
    [ -n "$1" ] || return 1
    # A live logcat reader initially replays its buffer, including records older
    # than the last baseline line. Exclude ALL baseline records, not just last.
    case "
$BASE_RECORDS
" in *"
$1
"*) return 1;; esac
    return 0
}

# Strict signed decimal -> tenths, without awk, floating point, or octal input.
# Validate the entire token before arithmetic; never accept a numeric prefix.
decimal_tenths() {
    _number=$1; _sign=1
    case "$_number" in -*) _sign=-1; _number=${_number#-};; esac
    case "$_number" in *.*) _whole=${_number%%.*}; _fraction=${_number#*.};; *) _whole=$_number; _fraction=0;; esac
    case "$_whole" in ''|*[!0-9]*) return 1;; esac
    case "$_fraction" in ''|*[!0-9]*) return 1;; esac
    while [ "${_whole#0}" != "$_whole" ]; do _whole=${_whole#0}; done
    [ -n "$_whole" ] || _whole=0
    [ "${#_whole}" -le 3 ] || return 1
    _fraction=${_fraction%"${_fraction#?}"}
    NUMBER_TENTHS=$(( _sign * (_whole * 10 + _fraction) ))
}

parse_eco() {
    _raw=${ECO_LINE#*\"outTemperature\"}; _raw=${_raw#*:}
    _raw=${_raw#"${_raw%%[![:space:]]*}"}
    _raw=${_raw%%,*}; _raw=${_raw%%\}*}; _raw=${_raw%% *}
    decimal_tenths "$_raw" || return 1
    [ "$NUMBER_TENTHS" -ge -500 ] && [ "$NUMBER_TENTHS" -le 600 ] || return 1
    # Uploaded Nov 17-22 logs repeatedly show this initialization value
    # immediately after dashboard temp=-1/unit=-1. It cannot decide by itself.
    if [ "$NUMBER_TENTHS" = -400 ]; then
        log 'reject ECO -40C startup value; waiting for ready dashboard temperature'
        return 1
    fi
    CANDIDATE_F=$(( (NUMBER_TENTHS * 9 + 1600) / 50 ))
    CANDIDATE_SOURCE=eco
}

parse_ui() {
    _raw=${UI_LINE#*temp = }; _raw=${_raw%% *}
    decimal_tenths "$_raw" || return 1
    _temperature=$NUMBER_TENTHS
    case "$UI_LINE" in
        *'tempunit = '*)
            _unit=${UI_LINE##*tempunit = }; _unit=${_unit%% *}
            case "$_unit" in 1|1.0) _unit=1;; 2|2.0) _unit=2;; *) return 1;; esac;;
        *)
            # Compatibility fallback only when the unit field is absent.
            [ "$_temperature" != -10 ] && [ "$_temperature" != -400 ] || return 1
            if [ "$UI_IS_C" = 1 ]; then _unit=1; else _unit=2; fi;;
    esac
    if [ "$_unit" = 1 ]; then
        [ "$_temperature" -ge -450 ] && [ "$_temperature" -le 600 ] || return 1
        CANDIDATE_F=$(( (_temperature * 9 + 1600) / 50 ))
    else
        [ "$_temperature" -ge -500 ] && [ "$_temperature" -le 1400 ] || return 1
        CANDIDATE_F=$(( _temperature / 10 ))
    fi
    CANDIDATE_SOURCE=dashboard-unit-$_unit
}

case "$MAX_WAIT" in ''|*[!0-9]*|0*) MAX_WAIT=120;; esac
[ "$MAX_WAIT" -le 600 ] || MAX_WAIT=120
if [ "$COOL_ENABLED" = "1" ] && [ "$COOL_ABOVE_F" -le "$THRESH_F" ]; then
    log "invalid thresholds: cool-above must exceed heat-below; no action"
    _copy_usb; exit 0
fi
START_UPTIME=$(clock_seconds) || { log 'kernel uptime unavailable; no action'; _copy_usb; exit 0; }
RETRY_AFTER=180
RETRY_WINDOW=60
SAMPLE_MAX_AGE=30
RETRY_AT=$(( START_UPTIME + RETRY_AFTER ))
FINAL_DEADLINE=$(( RETRY_AT + RETRY_WINDOW ))
# Snapshot the pre-existing buffer before listening. Old entries replayed by
# logcat are excluded by their complete baseline identities.
read_sources
BASE_ECO=$ECO_LINE; BASE_UI=$UI_LINE
BASE_RECORDS=$_records
umask 077
mkdir -p /dev/seat-comfort || exit 1
CAPTURE_DIR=/dev/seat-comfort/temperature.$$
mkdir "$CAPTURE_DIR" || exit 1
CAPTURE=$CAPTURE_DIR/records.log
# These are the two actual source tags observed on the supported US firmware.
# Native filtering avoids piping the entire live Android log through a shell.
logcat -v time 'SplitScreenClimateView:D' 'CoNA:I' '*:S' > "$CAPTURE" 2>/dev/null &
LISTENER_PID=$!
log "temperature baseline captured uptime=${START_UPTIME}s; existing records cannot trigger startup; reader=live-capture retry_at=${RETRY_AT}s"

TEMP_F=""
for ATTEMPT in 1 2; do
    if [ "$ATTEMPT" = 2 ]; then
        log "startup attempt 1 undecided; delayed retry scheduled uptime=${RETRY_AT}s"
        while :; do
            manual_stop
            NOW=$(clock_seconds) || { log 'kernel uptime unavailable; no action'; _copy_usb; exit 0; }
            [ "$NOW" -lt "$RETRY_AT" ] || break
            sleep 3
        done
        [ "$NOW" -lt "$FINAL_DEADLINE" ] || break
        # Do not use a first-attempt sample for delayed actuation.
        read_sources
        BASE_ECO=$ECO_LINE; BASE_UI=$UI_LINE
        BASE_RECORDS=$_records
        log "delayed startup retry began uptime=${NOW}s; fresh records required"
        WINDOW_END=$FINAL_DEADLINE
    else
        WINDOW_END=$RETRY_AT
    fi
    LAST_ECO=$BASE_ECO; LAST_UI=$BASE_UI
    PENDING_F=""; PENDING_SOURCE=""; PENDING_ACTION=""; PENDING_SINCE=0; PENDING_SEEN=0
    NOW=$(clock_seconds) || break
    SERVICE_DEADLINE=$(( NOW + MAX_WAIT ))
    if [ "$ATTEMPT" = 2 ] || [ "$SERVICE_DEADLINE" -gt "$WINDOW_END" ]; then SERVICE_DEADLINE=$WINDOW_END; fi
    SERVICES_READY=0
    while :; do
        manual_stop
        NOW=$(clock_seconds) || break
        [ "$NOW" -lt "$SERVICE_DEADLINE" ] || break
        if service check com.hkmc.vr 2>/dev/null | grep -q ': found' &&
           service check com.hkmc.micom.usm 2>/dev/null | grep -q ': found'; then
            SERVICES_READY=1; log "control services ready attempt=$ATTEMPT uptime=${NOW}s"; break
        fi
        sleep 2
    done
    if [ "$SERVICES_READY" != 1 ]; then
        log "control services not ready before deadline attempt=$ATTEMPT; no action"
        continue
    fi
    NOW=$(clock_seconds) || break
    TEMP_DEADLINE=$(( NOW + MAX_WAIT ))
    if [ "$ATTEMPT" = 2 ]; then TEMP_DEADLINE=$WINDOW_END
    elif [ "$TEMP_DEADLINE" -gt "$WINDOW_END" ]; then TEMP_DEADLINE=$WINDOW_END; fi
    while :; do
        manual_stop
        NOW=$(clock_seconds) || break
        [ "$NOW" -lt "$TEMP_DEADLINE" ] || break
        read_sources
        NOW=$(clock_seconds) || break
        [ "$NOW" -lt "$TEMP_DEADLINE" ] || break
        CANDIDATE_F=""; CANDIDATE_SOURCE=""; UI_NEW=0; ECO_NEW=0
        if [ "$UI_LINE" != "$LAST_UI" ] && new_record "$UI_LINE"; then
            UI_NEW=1; LAST_UI=$UI_LINE
        fi
        if [ "$ECO_LINE" != "$LAST_ECO" ] && new_record "$ECO_LINE"; then
            ECO_NEW=1; LAST_ECO=$ECO_LINE
        fi
        if [ "$UI_NEW" = 1 ]; then
            if ! parse_ui; then
                log "new dashboard temperature invalid/not ready attempt=$ATTEMPT; confirmation reset"
                PENDING_ACTION=""
            fi
        fi
        if [ -z "$CANDIDATE_F" ] && [ "$ECO_NEW" = 1 ]; then
            # A recent ready dashboard record remains authoritative over ECO.
            if [ "$UI_NEW" != 1 ] && [ -n "$PENDING_ACTION" ] &&
               [ "$PENDING_SOURCE" != eco ] && [ "$(( NOW - PENDING_SEEN ))" -le "$SAMPLE_MAX_AGE" ]; then
                :
            else
                parse_eco || :
            fi
        fi
        if [ -n "$CANDIDATE_F" ]; then
            temperature_action "$CANDIDATE_F"
            if [ "$ACTION" != "$PENDING_ACTION" ] || [ "$(( NOW - PENDING_SEEN ))" -gt "$SAMPLE_MAX_AGE" ]; then
                PENDING_SINCE=$NOW
            fi
            PENDING_F=$CANDIDATE_F; PENDING_SOURCE=$CANDIDATE_SOURCE
            PENDING_ACTION=$ACTION; PENDING_SEEN=$NOW
            log "temperature candidate=${PENDING_F}F action=$ACTION source=$PENDING_SOURCE attempt=$ATTEMPT uptime=${NOW}s; confirming action"
            D "candidate raw dashboard: $UI_LINE"
            D "candidate raw ECO: $ECO_LINE"
        fi
        # Missing/evicted records do not immediately discard a fresh valid
        # sample. A new invalid dashboard event does; samples expire after 30s.
        if [ -n "$PENDING_ACTION" ]; then
            if [ "$(( NOW - PENDING_SEEN ))" -gt "$SAMPLE_MAX_AGE" ]; then
                log "temperature sample expired attempt=$ATTEMPT; confirmation reset"
                PENDING_ACTION=""
            elif [ "$(( NOW - PENDING_SINCE ))" -ge 3 ]; then
                TEMP_F=$PENDING_F
                log "confirmed outside=${TEMP_F}F action=$PENDING_ACTION source=$PENDING_SOURCE attempt=$ATTEMPT uptime=${NOW}s"
                break
            fi
        fi
        sleep 3
    done
    [ -z "$TEMP_F" ] || break
    log "no fresh stable action before temperature deadline attempt=$ATTEMPT; no action"
done
[ -z "$TEMP_F" ] && { log 'startup temperature attempts exhausted; no action'; _copy_usb; exit 0; }

# Share the manual-command lock only during actuation, not temperature waits.
# /dev is cleared on reboot, so an interrupted command cannot lock out future boots.
umask 077
mkdir -p /dev/seat-comfort || exit 1
LOCK=/dev/seat-comfort/actuation.lock
mkdir "$LOCK" 2>/dev/null || { log "seat command already active; skipping startup action"; exit 0; }
LOCK_HELD=1
# A manual request made while startup was waiting must remain authoritative.
# This marker lives in /dev, so the next head-unit boot starts a new session.
if [ -f /dev/seat-comfort/manual.override ]; then
    log "manual command already requested this boot; skipping pending startup action"
    _copy_usb; exit 0
fi
if [ "$TEMP_F" -lt "$THRESH_F" ]; then
    log "outside ${TEMP_F}F < ${THRESH_F}F -> applying heaters"
    if [ "$WHEEL" = "1" ]; then
        service call com.hkmc.vr 16 i32 1 >/dev/null 2>&1; log "wheel on (exit $?)"
    fi
    if [ "$SEAT_DRV" -ge 1 ] && [ "$SEAT_DRV" -le 3 ]; then
        _e=$(seat_enum "$SEAT_DRV")
        service call com.hkmc.micom.usm 213 i32 "$_e" >/dev/null 2>&1; log "driver heat enum=$_e (exit $?)"
    fi
    if [ "$SEAT_PASS" -ge 1 ] && [ "$SEAT_PASS" -le 3 ]; then
        _e=$(seat_enum "$SEAT_PASS")
        service call com.hkmc.micom.usm 214 i32 "$_e" >/dev/null 2>&1; log "passenger heat enum=$_e (exit $?)"
    fi
elif [ "$COOL_ENABLED" = "1" ] && [ "$TEMP_F" -gt "$COOL_ABOVE_F" ]; then
    log "outside ${TEMP_F}F > ${COOL_ABOVE_F}F -> applying ventilation"
    if [ "$VENT_DRV" -ge 1 ] && [ "$VENT_DRV" -le 3 ]; then
        _e=$(vent_enum "$VENT_DRV")
        service call com.hkmc.micom.usm 213 i32 "$_e" >/dev/null 2>&1; log "driver ventilation enum=$_e (exit $?)"
    fi
    if [ "$VENT_PASS" -ge 1 ] && [ "$VENT_PASS" -le 3 ]; then
        _e=$(vent_enum "$VENT_PASS")
        service call com.hkmc.micom.usm 214 i32 "$_e" >/dev/null 2>&1; log "passenger ventilation enum=$_e (exit $?)"
    fi
else
    log "outside ${TEMP_F}F; no startup action (heat-below=$THRESH_F cool-enabled=$COOL_ENABLED cool-above=$COOL_ABOVE_F)"
fi
log "done"
_copy_usb
exit 0
