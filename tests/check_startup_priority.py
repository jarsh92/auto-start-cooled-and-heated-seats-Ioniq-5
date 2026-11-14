"""Replay the reported delayed-startup/manual-test race with real shell scripts."""
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    base = Path(folder)
    state = base / 'state'; state.mkdir()
    locks = base / 'locks'
    tools = base / 'bin'; tools.mkdir()
    calls = base / 'calls'; calls.write_text('')
    ready = base / 'temperature-ready'
    seen = base / 'logcat-seen'
    for key, value in dict(enabled=1, threshold_f=62, wheel=1, seat_drv=3, seat_pass=3,
                           cool_enabled=1, cool_above_f=67, vent_drv=3, vent_pass=0,
                           diag=1, max_wait=12).items():
        (state / key).write_text(str(value) + '\n')
    (tools / 'service').write_text('''#!/bin/sh
if [ "$1" = check ]; then echo "$2: found"; exit 0; fi
echo "$*" >> "$CALL_LOG"
echo "Result: Parcel(00000000    '....')"
''')
    (tools / 'logcat').write_text('''#!/bin/sh
touch "$LOGCAT_SEEN"
if [ -f "$TEMP_READY" ]; then echo '"outTemperature":20,'; fi
''')
    # Saving must work even if this utility is unavailable, as on a limited toolbox.
    (tools / 'mv').write_text('#!/bin/sh\necho "mv unavailable" >&2\nexit 127\n')
    for file in tools.iterdir(): file.chmod(0o700)
    path = str(tools) + ':/usr/bin:/bin'
    env = dict(os.environ, CALL_LOG=str(calls), LOGCAT_SEEN=str(seen), TEMP_READY=str(ready))
    startup = base / 'startup.sh'
    startup.write_text((ROOT / 'package/svc/auto-seat.sh').read_text()
        .replace('export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin', 'export PATH=' + path)
        .replace('STATE=/data/nemesis/state/$TAG', 'STATE=' + str(state))
        .replace('/dev/seat-comfort', str(locks)))
    manual = base / 'manual.sh'
    manual.write_text((ROOT / 'package/scripts/seat-action.sh').read_text()
        .replace('export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin', 'export PATH=' + path)
        .replace('STATE=/data/nemesis/state/coldstart.heat', 'STATE=' + str(state))
        .replace('LOCKBASE=/dev/seat-comfort', 'LOCKBASE=' + str(locks)))
    boot = subprocess.Popen(['sh', str(startup)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 5
    while not seen.exists():
        assert time.monotonic() < deadline, 'Startup did not reach temperature wait'
        time.sleep(0.01)
    heat = subprocess.run(['sh', str(manual), 'heat', '1', '3', '3'], env=env, capture_output=True, text=True)
    assert heat.returncode == 0, (heat.stdout, heat.stderr)
    assert (locks / 'manual.override').exists()
    assert calls.read_text().splitlines() == [
        'call com.hkmc.vr 16 i32 1',
        'call com.hkmc.micom.usm 213 i32 8',
        'call com.hkmc.micom.usm 214 i32 8']
    ready.touch()
    stdout, stderr = boot.communicate(timeout=8)
    assert boot.returncode == 0, (stdout, stderr)
    assert 'skipping pending startup action' in stdout
    assert len(calls.read_text().splitlines()) == 3, 'Startup overwrote manual heat'
    assert not (locks / 'actuation.lock').exists()

    # Simulate a fresh boot by clearing the volatile manual marker.
    (locks / 'manual.override').unlink()
    calls.write_text('')
    save = subprocess.run(['sh', str(manual), 'save', '1', '62', '1', '3', '3', '0', '1', '67', '3', '0', '1'],
                          env=env, capture_output=True, text=True)
    assert save.returncode == 0, (save.stdout, save.stderr)
    assert not (locks / 'manual.override').exists(), 'Saving alone must not suppress startup'
    assert (state / 'seat_pass').read_text().strip() == '3'
    warm = subprocess.run(['sh', str(startup)], env=env, capture_output=True, text=True, timeout=8)
    assert warm.returncode == 0, (warm.stdout, warm.stderr)
    assert calls.read_text().splitlines() == ['call com.hkmc.micom.usm 213 i32 5']
    assert not (locks / 'actuation.lock').exists()
print('PASS: delayed startup cannot undo manual heat; save works without mv; normal startup still ventilates')
