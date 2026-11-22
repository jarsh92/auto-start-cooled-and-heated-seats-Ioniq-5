"""Run the actual startup shell with simulated logcat, binder and kernel uptime.

Only host paths/PATH are redirected. No real vehicle commands are executed.
The fake clock makes deadlines deterministic, including expensive logcat polls.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'package/svc/auto-seat.sh').read_text()
MOCK = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
b = Path(os.environ['SIM']); cfg = json.loads((b/'scenario').read_text())
clock = b/'uptime'; now = int(clock.read_text().split('.')[0]); cmd = Path(sys.argv[0]).name
if cmd == 'sleep':
    now += int(sys.argv[1]); clock.write_text(str(now)+'.00 0.00\\n')
    if now >= cfg.get('manual_at', 10000):
        (b/'locks').mkdir(exist_ok=True); (b/'locks/manual.override').touch()
elif cmd == 'logcat':
    frame = {'at': 0}
    for candidate in cfg['frames']:
        if candidate['at'] <= now: frame = candidate
    for key, prefix in [('eco', ''), ('ui', 'setOutsideTempUIAdvanced::temp = ')]:
        if key in frame: print('11-22 12:00:%02d.000 100 200 I Sim: '%frame['at'] + prefix + frame[key])
    clock.write_text(str(now+cfg.get('scan_seconds', 0))+'.00 0.00\\n')
elif cmd == 'service':
    if sys.argv[1] == 'check':
        if now < cfg.get('service_ready_at', 0): print(sys.argv[2]+': not ready')
        else: print(sys.argv[2]+': found')
    else:
        with (b/'calls').open('a') as f: f.write(' '.join(sys.argv[1:])+'\\n')
        print("Result: Parcel(00000000 '....')")
'''


def replay(frames, settings=None, **options):
    with tempfile.TemporaryDirectory(prefix='seat-temperature-') as tmp:
        b = Path(tmp); state = b/'state'; state.mkdir(); (b/'bin').mkdir()
        values = dict(enabled=1, threshold_f=62, wheel=1, seat_drv=3, seat_pass=0,
                      cool_enabled=1, cool_above_f=67, vent_drv=3, vent_pass=0,
                      ui_temp_is_c=0, diag=1, max_wait=24)
        values.update(settings or {})
        for key, value in values.items(): (state/key).write_text(str(value)+'\n')
        (b/'scenario').write_text(json.dumps(dict(frames=frames, **options)))
        (b/'uptime').write_text('0.00 0.00\n'); (b/'calls').write_text('')
        for command in ['service', 'logcat', 'sleep']:
            p=b/'bin'/command; p.write_text(MOCK); p.chmod(0o700)
        (b/'bin/sync').write_text('#!/bin/sh\nexit 0\n'); (b/'bin/sync').chmod(0o700)
        script = SOURCE.replace('export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin',
                                'export PATH='+str(b/'bin')+':'+os.environ['PATH'])
        script = script.replace('STATE=/data/nemesis/state/$TAG', 'STATE='+str(state))
        script = script.replace('/dev/seat-comfort', str(b/'locks'))
        script = script.replace('/proc/uptime', str(b/'uptime'))
        (b/'startup.sh').write_text(script)
        result = subprocess.run(['sh',str(b/'startup.sh')],env=dict(os.environ,SIM=str(b)),
                                capture_output=True,text=True,timeout=15)
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert not result.stderr, result.stderr
        calls=(b/'calls').read_text().splitlines()
        assert not (b/'locks/actuation.lock').exists(), 'Leaked actuation lock'
        return calls, result.stdout, int((b/'uptime').read_text().split('.')[0])


class StartupTemperature(unittest.TestCase):
    VENT = ['call com.hkmc.micom.usm 213 i32 5']
    HEAT = ['call com.hkmc.vr 16 i32 1', 'call com.hkmc.micom.usm 213 i32 8']

    def test_reported_minus40_then_dashboard_73(self):
        calls, log, _ = replay([{'at':0},{'at':3,'eco':'"outTemperature":-40,','ui':'-1.0 / tempunit = -1'},
                               {'at':6,'eco':'"outTemperature":-40,','ui':'73.0 / tempunit = 2'}])
        self.assertEqual(calls,self.VENT); self.assertIn('reject ECO -40C',log)
        self.assertIn('confirmed outside=73F source=dashboard-unit-2',log)

    def test_minus40_alone_never_heats(self):
        calls, log, elapsed = replay([{'at':0},{'at':3,'eco':'"outTemperature":-40,'}])
        self.assertEqual(calls,[]); self.assertIn('no fresh stable',log); self.assertEqual(elapsed,24)

    def test_dashboard_wins_over_conflicting_eco(self):
        calls,_,_=replay([{'at':0},{'at':3,'eco':'"outTemperature":0,','ui':'73 / tempunit = 2'}])
        self.assertEqual(calls,self.VENT)

    def test_decimal_json_whitespace_and_celsius(self):
        calls,_,_=replay([{'at':0},{'at':3,'eco':'"outTemperature" : 23.0, '}])
        self.assertEqual(calls,self.VENT)
        calls,_,_=replay([{'at':0},{'at':3,'ui':'23.0 / tempunit = 1'}])
        self.assertEqual(calls,self.VENT)

    def test_real_cold_and_negative_temperatures(self):
        for eco in ['0','-1','-10.5']:
            with self.subTest(eco=eco):
                calls,_,_=replay([{'at':0},{'at':3,'eco':'"outTemperature":'+eco+','}])
                self.assertEqual(calls,self.HEAT)
        # Explicit ready dashboard units allow genuine -40, unlike uncorroborated ECO.
        calls,_,_=replay([{'at':0},{'at':3,'ui':'-40.0 / tempunit = 1','eco':'"outTemperature":-40,'}])
        self.assertEqual(calls,self.HEAT)

    def test_stale_records_do_not_trigger(self):
        calls,log,_=replay([{'at':0,'ui':'73 / tempunit = 2','eco':'"outTemperature":23,'}])
        self.assertEqual(calls,[]); self.assertIn('no fresh stable',log)

    def test_transient_cold_changes_before_confirmation(self):
        calls,log,_=replay([{'at':0},{'at':3,'ui':'58 / tempunit = 2'},
                           {'at':6,'ui':'73 / tempunit = 2'}])
        self.assertEqual(calls,self.VENT); self.assertNotIn('applying heaters',log)

    def test_invalid_sample_resets_confirmation(self):
        calls,_,elapsed=replay([{'at':0},{'at':3,'ui':'73 / tempunit = 2'},
                                {'at':6,'ui':'-1 / tempunit = -1'},
                                {'at':9,'ui':'73 / tempunit = 2'}])
        self.assertEqual(calls,self.VENT); self.assertGreaterEqual(elapsed,12)

    def test_boundaries_and_neutral_band(self):
        for value in [62,64,67]:
            with self.subTest(value=value):
                calls,log,_=replay([{'at':0},{'at':3,'ui':str(value)+' / tempunit = 2'}])
                self.assertEqual(calls,[]); self.assertIn('no startup action',log)

    def test_declared_unit_overrides_saved_unit(self):
        calls,_,_=replay([{'at':0},{'at':3,'ui':'73 / tempunit = 2'}],dict(ui_temp_is_c=1))
        self.assertEqual(calls,self.VENT)

    def test_missing_unit_fallback_and_not_ready(self):
        calls,_,_=replay([{'at':0},{'at':3,'ui':'23.0'}],dict(ui_temp_is_c=1))
        self.assertEqual(calls,self.VENT)
        for raw in ['-1','-40','-1 / tempunit = -1','73 / tempunit = 0','73 / tempunit = garbage']:
            with self.subTest(raw=raw):
                calls,_,_=replay([{'at':0},{'at':3,'ui':raw}]); self.assertEqual(calls,[])

    def test_malformed_json_is_not_numeric_prefix(self):
        for raw in ['--40','23garbage','1.2.3','9999','61','null','1e2','']:
            with self.subTest(raw=raw):
                calls,_,_=replay([{'at':0},{'at':3,'eco':'"outTemperature":'+raw+','}])
                self.assertEqual(calls,[])

    def test_manual_request_while_waiting(self):
        calls,log,_=replay([{'at':0},{'at':12,'ui':'73 / tempunit = 2'}],manual_at=6)
        self.assertEqual(calls,[]); self.assertIn('manual command already requested',log)

    def test_services_timeout_and_late_ready(self):
        calls,log,elapsed=replay([{'at':0},{'at':3,'ui':'73 / tempunit = 2'}],service_ready_at=100)
        self.assertEqual(calls,[]); self.assertEqual(elapsed,24); self.assertIn('services not ready',log)
        calls,_,_=replay([{'at':0},{'at':3,'ui':'73 / tempunit = 2'}],service_ready_at=10)
        self.assertEqual(calls,self.VENT)

    def test_expensive_logcat_counts_toward_deadline(self):
        calls,log,elapsed=replay([{'at':0},{'at':1,'ui':'73 / tempunit = 2'}],scan_seconds=12)
        self.assertEqual(calls,[]); self.assertIn('no fresh stable',log)
        self.assertLessEqual(elapsed,48)  # baseline + deadline + one in-flight scan

    def test_diagnostics_off_disabled_and_cooling_off(self):
        frames=[{'at':0},{'at':3,'ui':'73 / tempunit = 2'}]
        calls,_,_=replay(frames,dict(diag=0)); self.assertEqual(calls,self.VENT)
        calls,_,_=replay(frames,dict(enabled=0)); self.assertEqual(calls,[])
        calls,_,_=replay(frames,dict(cool_enabled=0)); self.assertEqual(calls,[])


if __name__ == '__main__': unittest.main(verbosity=2)
