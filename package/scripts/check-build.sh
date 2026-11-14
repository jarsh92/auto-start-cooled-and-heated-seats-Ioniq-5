#!/system/bin/sh
# Personal build: commands derived from this exact framework build.
export PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
BUILD=$(getprop ro.build.version.incremental)
if [ "$BUILD" != "eng.vmadmin.20260903.161833" ]; then
    echo "Unsupported head-unit build: $BUILD"
    echo "This package was prepared for eng.vmadmin.20260903.161833."
    exit 1
fi
exit 0
