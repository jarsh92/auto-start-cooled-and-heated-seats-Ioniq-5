#!/system/bin/sh
# Sourced only by lifecycle hooks; no NEMESIS registry edits.
LEGACY=/data/nemesis/apps/coldstart.heat
CURRENT=/data/nemesis/apps/auto-seat
bridge_install() {
    [ ! -e "$LEGACY" ] && [ ! -L "$LEGACY" ] || return 1
    mkdir -p "$LEGACY/scripts" || return 1
    cp "$CURRENT/scripts/seat-action.sh" "$LEGACY/scripts/seat-action.sh" || return 1
    echo auto-seat-bridge-v1 > "$LEGACY/auto-seat.bridge" || return 1
    cmp "$CURRENT/scripts/seat-action.sh" "$LEGACY/scripts/seat-action.sh" || return 1
    chmod 755 "$LEGACY" "$LEGACY/scripts" "$LEGACY/scripts/seat-action.sh"
}
bridge_remove() {
    [ -d "$LEGACY" ] && [ ! -L "$LEGACY" ] || return 1
    [ "$(cat "$LEGACY/auto-seat.bridge" 2>/dev/null)" = auto-seat-bridge-v1 ] || return 1
    [ ! -e "$LEGACY/NEMESIS.data" ] || return 1
    [ ! -L "$LEGACY/scripts" ] && [ ! -L "$LEGACY/scripts/seat-action.sh" ] || return 1
    cmp "$CURRENT/scripts/seat-action.sh" "$LEGACY/scripts/seat-action.sh" || return 1
    # rmdir refuses unknown files. Never recursively delete a legacy package here.
    rm "$LEGACY/scripts/seat-action.sh" "$LEGACY/auto-seat.bridge" || return 1
    rmdir "$LEGACY/scripts" "$LEGACY"
}
