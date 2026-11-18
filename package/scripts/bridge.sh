#!/system/bin/sh
# Sourced only by lifecycle hooks; no NEMESIS registry edits.
LEGACY=/data/nemesis/apps/coldstart.heat
CURRENT=/data/nemesis/apps/autoseat.heat
bridge_install() {
    [ ! -e "$LEGACY" ] && [ ! -L "$LEGACY" ] || return 1
    mkdir "$LEGACY" || return 1
    # Mark ownership before payload copying, so an interrupted copy is recoverable.
    echo autoseat.heat-bridge-v1 > "$LEGACY/autoseat.heat.bridge" || return 1
    mkdir "$LEGACY/scripts" || return 1
    cp "$CURRENT/scripts/seat-action.sh" "$LEGACY/scripts/seat-action.sh" || return 1
    cmp "$CURRENT/scripts/seat-action.sh" "$LEGACY/scripts/seat-action.sh" || return 1
    chmod 755 "$LEGACY" "$LEGACY/scripts" "$LEGACY/scripts/seat-action.sh"
}
bridge_remove() {
    # Postinstall can fail before it creates a bridge; uninstall must still work.
    if [ ! -e "$LEGACY" ] && [ ! -L "$LEGACY" ]; then return 0; fi
    [ -d "$LEGACY" ] && [ ! -L "$LEGACY" ] || return 1
    [ ! -L "$LEGACY/autoseat.heat.bridge" ] || return 1
    [ "$(cat "$LEGACY/autoseat.heat.bridge" 2>/dev/null)" = autoseat.heat-bridge-v1 ] || return 1
    [ ! -e "$LEGACY/NEMESIS.data" ] || return 1
    [ ! -L "$LEGACY/scripts" ] && [ ! -L "$LEGACY/scripts/seat-action.sh" ] || return 1
    for entry in "$LEGACY"/* "$LEGACY"/.[!.]* "$LEGACY"/..?*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        case "$entry" in "$LEGACY/scripts"|"$LEGACY/autoseat.heat.bridge") ;; *) return 1;; esac
    done
    if [ -e "$LEGACY/scripts" ]; then
        [ -d "$LEGACY/scripts" ] || return 1
        for entry in "$LEGACY/scripts"/* "$LEGACY/scripts"/.[!.]* "$LEGACY/scripts"/..?*; do
            [ -e "$entry" ] || [ -L "$entry" ] || continue
            [ "$entry" = "$LEGACY/scripts/seat-action.sh" ] && [ -f "$entry" ] || return 1
        done
        # Only an owned helper (possibly an interrupted partial copy) is removed.
        if [ -e "$LEGACY/scripts/seat-action.sh" ]; then
            rm "$LEGACY/scripts/seat-action.sh" || return 1
        fi
        rmdir "$LEGACY/scripts" || return 1
    fi
    rm "$LEGACY/autoseat.heat.bridge" || return 1
    rmdir "$LEGACY"
}
