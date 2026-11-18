from pathlib import Path
import ctypes, hashlib, json, os, re, shlex, shutil, subprocess, tempfile, zipfile

base=Path(__file__).resolve().parents[1]
shell=os.environ.get('AUTO_SEAT_TEST_SHELL','sh')
SHELL=[shell] if Path(shell).name.lower() in ['sh','bash','dash','sh.exe','bash.exe'] else [shell,'sh']
pkg=base/'package'
kit=base/'usb'
rows=[]
for p in [*pkg.rglob('*.sh'),*kit.glob('*.sh')]:
    r=subprocess.run([*SHELL,'-n',str(p)],capture_output=True)
    assert r.returncode==0,(p,r.stderr)
rows.append({'test':'all shipped shell syntax','passed':True})
prefix='export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin'
with tempfile.TemporaryDirectory(prefix='clean-seat-') as tmp:
    f=Path(tmp)
    paths={'/data/nemesis':(f/'data').as_posix(),'/dev/seat-comfort':(f/'locks').as_posix()}
    calls=f/'calls'
    def adapt(code):
        code=re.sub(r'(?m)^export PATH=.*$','',code)
        for old,new in paths.items():code=code.replace(old,new)
        code=code.replace(prefix,'')
        code=code.replace('export PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin','')
        return code
    def run(code,*args,want=0,extra=''):
        body='''getprop() { if [ "$1" = sys.boot_completed ]; then echo 1; else echo eng.vmadmin.20260903.161833; fi; }
service() {
    if [ "$1" = check ]; then echo "$2: found"; return 0; fi
    echo "$*" >> CALLS
    echo "Result: Parcel(00000000 '....')"
}
'''.replace('CALLS',shlex.quote(calls.as_posix()))+extra+'\n'+adapt(code)
        script=f/'test.sh';script.write_text(body,newline='\n')
        r=subprocess.run([*SHELL,str(script),*args],capture_output=True,text=True)
        assert r.returncode==want,(r.returncode,r.stdout,r.stderr)
        return r
    pre=(pkg/'scripts/check-build.sh').read_text()
    run(pre,extra='getprop() { echo wrong-build; }',want=1)
    legacy=f/'data/apps/coldstart.heat';legacy.mkdir(parents=True)
    run(pre,want=1)
    legacy.rmdir()
    run(pre)
    rows.append({'test':'firmware/legacy-directory guards and clean preinstall','passed':True})
    current=f/'data/apps/autoseat.heat'
    shutil.copytree(pkg,current)
    # Lifecycle hooks source their helper by absolute path. Adapt only a host copy.
    bridge=current/'scripts/bridge.sh';bridge.write_text(adapt(bridge.read_text()),newline='\n')
    oldhold=f/'data/backup/auto-seat-migration-v1/HOLD';oldhold.parent.mkdir(parents=True);oldhold.write_text('old transaction retained')
    run((pkg/'scripts/post.sh').read_text())
    state=f/'data/state/coldstart.heat'
    assert (state/'enabled').read_text().strip()=='1'
    assert (state/'threshold_f').read_text().strip()=='50'
    assert (legacy/'autoseat.heat.bridge').read_text().strip()=='autoseat.heat-bridge-v1'
    assert (legacy/'scripts/seat-action.sh').read_bytes()==(current/'scripts/seat-action.sh').read_bytes()
    rows.append({'test':'fresh defaults and exact APK helper despite retained old HOLD','passed':True})
    helper=(pkg/'scripts/seat-action.sh').read_text()
    assert 'CONFIG_READ' in run(helper,'read').stdout
    run(helper,'save','1','62','1','3','2','0','1','77','2','1','0')
    assert (state/'threshold_f').read_text().strip()=='62'
    for command,level,expected in [('driver_heat','3','call com.hkmc.micom.usm 213 i32 8'),('passenger','2','call com.hkmc.micom.usm 214 i32 4')]:
        calls.write_text('');run(helper,command,level)
        assert calls.read_text().splitlines()==[expected]
    calls.write_text('');run(helper,'off')
    assert len(calls.read_text().splitlines())==3
    run(helper,'driver_heat','9',want=1)
    rows.append({'test':'read/save/isolated heat/vent/off and invalid input with old HOLD present','passed':True})
    (state/'enabled').write_text('0\n');calls.write_text('')
    run((pkg/'svc/auto-seat.sh').read_text())
    assert calls.read_text()==''
    rows.append({'test':'disabled startup sends no controls despite old HOLD','passed':True})
    (state/'enabled').write_text('1\n')
    (f/'locks/manual.override').unlink()
    calls.write_text('')
    run((pkg/'svc/auto-seat.sh').read_text(),extra="""logcat() { echo '"outTemperature":30,'; }
""")
    assert calls.read_text().splitlines()==['call com.hkmc.micom.usm 213 i32 4','call com.hkmc.micom.usm 214 i32 3']
    rows.append({'test':'warm startup ventilation works with retained old HOLD','passed':True})
    # Unknown helper files must block removal without partial cleanup.
    (legacy/'unknown').write_text('retain')
    run((pkg/'scripts/preun.sh').read_text(),want=1)
    assert (legacy/'scripts/seat-action.sh').exists()
    (legacy/'unknown').unlink()
    before={p.name:p.read_bytes() for p in state.iterdir() if p.is_file()}
    run((pkg/'scripts/preun.sh').read_text())
    assert not legacy.exists()
    assert before=={p.name:p.read_bytes() for p in state.iterdir() if p.is_file()}
    assert oldhold.read_text()=='old transaction retained'
    rows.append({'test':'owned helper cleanup preserves settings/backups; unknown files rejected','passed':True})
    # Test the complete installer stop gates with fake read-only Android queries.
    installer=(kit/'clean-install.sh').read_text().replace('NEM=/system/xbin/nemesis','NEM=nem_mock')
    installer=installer.replace('/proc/$$/status',(f/'proc-status').as_posix())
    (f/'proc-status').write_text('Uid: 0 0 0 0\n')
    for id in ['coldstart.heat','auto-seat','autoseat.heat']:
        stub='nem_mock() { [ "$1" = pkg-list ] && { echo "'+id+'|Auto Seat|0|application,service|2.0|"; return 0; }; echo unexpected-call >&2; return 99; }\n'
        got=run(installer,want=1,extra=stub)
        assert 'still installed' in got.stdout
    rows.append({'test':'installer refuses all existing seat IDs without automatic uninstall','passed':True})

# Wrapper stays in the USB directory and logs both success and failure.
for status in [0,7]:
    with tempfile.TemporaryDirectory(prefix='clean-log-') as tmp:
        f=Path(tmp)
        wrapper=(kit/'NEMESIS.sh').read_text().replace('/system/bin/sh ./clean-install.sh',' '.join(shlex.quote(x) for x in SHELL)+' ./clean-install.sh')
        (f/'NEMESIS.sh').write_text(wrapper,newline='\n')
        (f/'clean-install.sh').write_text('echo stub-install\nexit '+str(status)+'\n',newline='\n')
        r=subprocess.run([*SHELL,str(f/'NEMESIS.sh')],capture_output=True)
        assert r.returncode==status
        assert 'Installer exit code: '+str(status) in (f/'Auto-Seat-Clean-Install.log').read_text()
rows.append({'test':'wrapper log, cwd and success/failure exit propagation','passed':True})

# Check actual POSIX creation modes and mask scope. Windows shell emulation
# cannot establish Linux/Android filesystem permissions.
if os.name != 'nt':
    with tempfile.TemporaryDirectory(prefix='seat-mask-') as folder:
        p=Path(folder)
        result=subprocess.run([*SHELL,'-c', 'umask 077; (umask 022; mkdir "$1/public"); mkdir "$1/private"; umask', 'mask-test',str(p)],capture_output=True,text=True,check=True)
        assert p.joinpath('public').stat().st_mode & 0o777 == 0o755
        assert p.joinpath('private').stat().st_mode & 0o777 == 0o700
        assert int(result.stdout.strip(),8)==0o77
    rows.append({'test':'actual POSIX directory modes and scoped mask','passed':True})
out=base/'dist';out.mkdir(exist_ok=True)
(out/'clean-lifecycle-tests.json').write_text(json.dumps({'checks':rows,'actual_android_nemesis_tested':False,'posix_permission_check_run':os.name!='nt','passed':True},indent=2)+'\n')
print('PASS',len(rows),'clean package/lifecycle/control/wrapper checks; actual Android/NEMESIS still require vehicle evidence.')
