"""Regression checks for real helper behavior, using a fake service and temp paths."""
import itertools, os, shlex, subprocess, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    base=Path(folder);classes=base/'classes';classes.mkdir()
    subprocess.run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-d',str(classes),str(ROOT/'app/src/com/nemesis/coldstart/SeatCommands.java'),str(ROOT/'tests/CommandProbe.java')],check=True)
    def request(*args):
        r=subprocess.check_output(['java','-cp',str(classes),'com.nemesis.coldstart.CommandProbe',*map(str,args)],text=True)
        assert len(r.encode())<=512
        return r
    state=base/'state';state.mkdir();locks=base/'locks';log=base/'calls';log.write_text('')
    service=base/'service'
    service.write_text('''#!/bin/sh
printf '%s\n' "$*" >> "$CALL_LOG"
[ -n "$FAKE_DELAY" ] && sleep "$FAKE_DELAY"
case "$*" in *" $FAIL_TRANSACTION i32 "*) [ -n "$FAIL_TRANSACTION" ] && { echo 'Parcel(error)'; exit 1; };; esac
echo 'Parcel(00000000 00000000)'
''');service.chmod(0o700)
    helper=base/'helper.sh'
    code=(ROOT/'package/scripts/seat-action.sh').read_text().replace('export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin','export PATH=/usr/bin:/bin').replace('STATE=/data/nemesis/state/coldstart.heat','STATE='+str(state)).replace('LOCKBASE=/dev/seat-comfort','LOCKBASE='+str(locks)).replace('SERVICE=service','SERVICE='+str(service))
    helper.write_text(code)
    env=dict(os.environ,CALL_LOG=str(log))
    def run(req, overrides=None):
        # Exercise the production script body using exactly the generated mode arguments.
        args=shlex.split(req)[2:]
        return subprocess.run(['sh',str(helper),*args],env=dict(env,**(overrides or {})),capture_output=True,text=True)
    def calls(): return log.read_text().splitlines()
    for wheel,driver,passenger in itertools.product([False,True],range(4),range(4)):
        log.write_text('');req=request('heat',str(wheel).lower(),driver,passenger)
        if not req: assert not wheel and driver==passenger==0;continue
        r=run(req);assert r.returncode==0,(r.stdout,r.stderr)
        expected=[]
        if wheel:expected.append('call com.hkmc.vr 16 i32 1')
        if driver:expected.append('call com.hkmc.micom.usm 213 i32 '+str(driver+5))
        if passenger:expected.append('call com.hkmc.micom.usm 214 i32 '+str(passenger+5))
        assert calls()==expected
    for driver,passenger in itertools.product(range(4),repeat=2):
        log.write_text('');req=request('vent',driver,passenger)
        if not req:assert driver==passenger==0;continue
        r=run(req);assert r.returncode==0,(r.stdout,r.stderr)
        expected=[]
        if driver:expected.append('call com.hkmc.micom.usm 213 i32 '+str(driver+2))
        if passenger:expected.append('call com.hkmc.micom.usm 214 i32 '+str(passenger+2))
        assert calls()==expected
    for mode,transaction in [('driver',213),('passenger',214)]:
        log.write_text('');assert run(request(mode,0)).returncode==0
        assert calls()==['call com.hkmc.micom.usm '+str(transaction)+' i32 2']
    # A single-seat heating request must never touch the other seat or wheel.
    for mode,transaction in [('driver_heat',213),('passenger_heat',214)]:
        for value in range(4):
            log.write_text('')
            (locks/'manual.override').unlink(missing_ok=True)
            assert run(request(mode,value)).returncode==0
            expected_value=2 if value==0 else value+5
            assert calls()==['call com.hkmc.micom.usm '+str(transaction)+' i32 '+str(expected_value)]
            assert (locks/'manual.override').read_text().strip()==mode
        for invalid in [-1,4]:
            rejected=subprocess.run(['java','-cp',str(classes),'com.nemesis.coldstart.CommandProbe',mode,str(invalid)],capture_output=True)
            assert rejected.returncode!=0
            bad=subprocess.run(['sh',str(helper),mode,str(invalid)],env=env,capture_output=True,text=True)
            assert bad.returncode!=0 and 'invalid seat level' in bad.stdout
    assert subprocess.run(['java','-cp',str(classes),'com.nemesis.coldstart.CommandProbe','oversize'],capture_output=True).returncode!=0
    log.write_text('');(locks/'manual.override').unlink(missing_ok=True)
    assert run(request('save')).returncode==0;assert not calls()
    assert not (locks/'manual.override').exists()
    assert (state/'threshold_f').read_text().strip()=='62'
    assert (state/'cool_above_f').read_text().strip()=='67'
    assert (state/'diag').read_text().strip()=='1'
    assert 'CONFIG_READ' in run(request('read')).stdout
    assert run(request('heat','true',3,3)).returncode==0
    assert 'BEGIN heat' in (state/'diag.log').read_text()
    assert 'transaction=213' in (state/'diag.log').read_text()
    log.write_text('')
    slow=subprocess.Popen(['sh',str(helper),'heat','1','3','3'],env=dict(env,FAKE_DELAY='0.15'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    deadline=time.monotonic()+3
    while not (locks/'actuation.lock').exists():
        assert time.monotonic()<deadline;time.sleep(0.005)
    blocked=run(request('vent',3,3));assert blocked.returncode!=0 and 'another seat command' in blocked.stdout
    slow.communicate(timeout=5);assert slow.returncode==0
    assert not (locks/'actuation.lock').exists()
    assert len(calls())==3
    log.write_text('');r=run(request('heat','true',3,3),{'FAIL_TRANSACTION':'213'})
    assert r.returncode!=0 and 'COMMANDS_ACCEPTED' not in r.stdout
    assert len(calls())==2 and not (locks/'actuation.lock').exists()
    log.write_text('');assert run(request('off'),{'FAIL_TRANSACTION':'16'}).returncode!=0
    assert len(calls())==3
    log.write_text('');bad=subprocess.run(['sh',str(helper),'heat','1','4','3'],env=env,capture_output=True)
    assert bad.returncode!=0 and not calls()
    old=(state/'threshold_f').read_text()
    bad=subprocess.run(['sh',str(helper),'save','1','62','1','3','3','0','1','60','3','0','1'],env=env,capture_output=True)
    assert bad.returncode!=0 and (state/'threshold_f').read_text()==old
print('PASS: 48 original combinations + 8 isolated single-seat heating levels; <=512-byte requests; save/read; manual logging; shared lock; error cleanup; Off; invalid settings')
