#!/system/bin/sh
export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
. /data/nemesis/apps/auto-seat/scripts/bridge.sh
bridge_remove || { echo "Bridge cleanup failed; stop and inspect."; exit 1; }
exit 0
