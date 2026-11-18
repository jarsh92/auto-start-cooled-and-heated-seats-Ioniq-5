#!/system/bin/sh
case "$0" in */*) cd "${0%/*}" || exit 1;; esac
if ! ( : > ./Auto-Seat-Clean-Install.log ); then echo 'STOP: cannot write USB log'; exit 1; fi
/system/bin/sh ./clean-install.sh >> ./Auto-Seat-Clean-Install.log 2>&1
result=$?
echo "Installer exit code: $result" >> ./Auto-Seat-Clean-Install.log
echo 'Auto Seat installation finished. Return Auto-Seat-Clean-Install.log.'
exit "$result"
