"""Real migration/hook shell code, filesystem fake NEMESIS; no vehicle connection."""
from pathlib import Path
import contextlib, json, os, shutil, subprocess, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'downloads/Ioniq5-auto-seat-2.0.zip'
PREFIX='export PATH=/data/nemesis/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin'
BUILD='eng.vmadmin.20260903.161833'
FAKE=r'''#!/usr/bin/python3
from pathlib import Path
import json, os, shutil, subprocess, sys, zipfile
r=Path(os.environ['TEST_ROOT']); args=sys.argv[1:]
db=r/'registry.json'; ids=json.loads(db.read_text())
with (r/'operations').open('a') as f: f.write(' '.join(args)+'\n')
fail=os.environ.get('FAIL','')
def save(): db.write_text(json.dumps(ids))
def hook(path):
    text=path.read_text().replace('/data/nemesis',str(r/'data'))
    text=text.replace('export PATH='+str(r/'data')+'/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin',
                      'export PATH='+str(r/'bin')+':/usr/bin:/bin')
    bridge=r/'data/apps/auto-seat/scripts/bridge.sh'
    if bridge.exists():
        temp=r/'bridge-runtime.sh'
        temp.write_text(bridge.read_text().replace('/data/nemesis',str(r/'data')))
        text=text.replace('. '+str(bridge),'. '+str(temp))
    return subprocess.run(['sh','-c',text],env=os.environ).returncode
op=args[0]
if op=='pkg-list':
    for id in ids: print(id+'|Auto Seat|0|application,service|2.0|')
elif op=='pkg-info':
    arg=args[1]
    if Path(arg).is_file():
        with zipfile.ZipFile(arg) as z: print(z.read('NEMESIS.data').decode())
    elif arg in ids: print('id='+arg)
    else: sys.exit(1)
elif op=='service':
    if args[1]=='list':
        for id in ids: print(id+'/apply|background|stopped|0')
        if os.environ.get('EXTRA_SERVICE'): print('coldstart.heat/extra|background|running|42')
    elif args[1]=='stop':
        if fail=='stop': sys.exit(1)
    else: sys.exit(99)
elif op=='uninstall':
    id=args[1]
    if fail=='uninstall': sys.exit(5)
    root=r/'data/apps'/id
    if id=='auto-seat' and hook(root/'scripts/preun.sh'): sys.exit(5)
    if id in ids: ids.remove(id); save()
    if root.exists(): shutil.rmtree(root)
    (r/'installed.apk').unlink(missing_ok=True)
elif op=='install':
    with zipfile.ZipFile(args[1]) as z:
        meta=z.read('NEMESIS.data').decode()
        id=[l[3:] for l in meta.splitlines() if l.startswith('id=')][0]
        if id=='auto-seat' and 'coldstart.heat' in ids: sys.exit(23)
        if id=='coldstart.heat' and 'auto-seat' in ids: sys.exit(23)
        if (fail=='install' and id=='auto-seat') or (fail=='recover-install' and id=='coldstart.heat'): sys.exit(1)
        dest=r/'data/apps'/id
        if id=='auto-seat' and (r/'data/apps/coldstart.heat').exists(): sys.exit(1)
        dest.mkdir(parents=True,exist_ok=True); z.extractall(dest)
        shutil.copyfile(dest/'app/auto-seat.apk',r/'installed.apk')
        ids.append(id); save()
        if id=='auto-seat':
            if fail=='postinstall': sys.exit(1)
            if hook(dest/'scripts/post.sh'): sys.exit(1)
        else:
            if hook(dest/'scripts/post.sh'): sys.exit(1)
else: sys.exit(99)
'''
def tree(path):
    return {str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}
class Fixture:
    def __init__(self,folder):
        self.r=Path(folder); self.data=self.r/'data'
        self.bundle=self.r/'usb'; self.bundle.mkdir()
        self.bin=self.r/'bin'; self.bin.mkdir()
        self.old=self.data/'apps/coldstart.heat'; self.new=self.data/'apps/auto-seat'
        self.state=self.data/'state/coldstart.heat'; self.state.mkdir(parents=True)
        self.back=self.data/'backup/auto-seat-migration-v1'
        self.lock=self.r/'dev/seat-comfort/actuation.lock'
        self.env=dict(os.environ,TEST_ROOT=str(self.r),PATH=str(self.bin)+':/usr/bin:/bin',BUILD=BUILD)
        with zipfile.ZipFile(RELEASE) as z:
            z.extractall(self.old); z.extractall(self.bundle/'original')
        shutil.copyfile(RELEASE,self.bundle/'original.zip')
        shutil.copyfile(self.old/'app/auto-seat.apk',self.r/'installed.apk')
        (self.r/'registry.json').write_text(json.dumps(['coldstart.heat']))
        (self.r/'operations').write_text('')
        values=dict(enabled=b'1\n',threshold_f=b'62\n',wheel=b'1\n',seat_drv=b'3\n',
            seat_pass=b'2\n',ui_temp_is_c=b'1\n',cool_enabled=b'1\n',cool_above_f=b'77\n',
            vent_drv=b'2\n',vent_pass=b'1\n',diag=b'0\n',max_wait=b'120\n',
            unknown_future_option=b'keep-me\n',**{'.hidden':b'\x00\xff\n'})
        for k,v in values.items(): (self.state/k).write_bytes(v)
        (self.state/'nested').mkdir(); (self.state/'nested/opaque').write_bytes(b'\x00more')
        self.before=tree(self.state)
        candidate=self.bundle/'candidate'; shutil.copytree(ROOT/'package',candidate)
        (candidate/'app').mkdir(exist_ok=True)
        shutil.copyfile(self.old/'app/auto-seat.apk',candidate/'app/auto-seat.apk')
        for n in ['LICENSE','CREDITS.md']: shutil.copyfile(ROOT/n,candidate/n)
        with zipfile.ZipFile(self.bundle/'candidate.zip','w') as z:
            for p in candidate.rglob('*'):
                if p.is_file(): z.write(p,p.relative_to(candidate))
        for name,body in {
            'nemesis':FAKE,
            'id':'#!/bin/sh\necho 0\n',
            'getprop':'#!/bin/sh\nif [ "$1" = sys.boot_completed ]; then echo "${BOOT:-1}"; else echo "$BUILD"; fi\n',
            'am':'#!/bin/sh\necho "am $*" >> "$TEST_ROOT/operations"\n',
            'pm':'#!/bin/sh\n[ -f "$TEST_ROOT/installed.apk" ] && echo "package:$TEST_ROOT/installed.apk"\n',
            'cp':'#!/bin/sh\ncase "$2" in *state-check*) [ "${FAIL:-}" = backup ] && exit 1;; esac\nexec /bin/cp "$@"\n',
            'service':'#!/bin/sh\necho "ACTUATOR $*" >> "$TEST_ROOT/operations"\nexit 99\n',
        }.items():
            (self.bin/name).write_text(body); (self.bin/name).chmod(0o755)
        code=(ROOT/'migration/migrate.sh').read_text()
        code=code.replace(PREFIX,'export PATH='+self.env['PATH'])
        code=code.replace('NEM=/system/xbin/nemesis','NEM='+str(self.bin/'nemesis'))
        code=code.replace('BASE=/data/nemesis','BASE='+str(self.data))
        code=code.replace('/dev/seat-comfort',str(self.r/'dev/seat-comfort'))
        self.script=self.bundle/'migrate.sh'; self.script.write_text(code)
    def run(self,action='check',token='',ok=True,**env):
        p=subprocess.run(['sh',str(self.script),action,token],cwd=self.bundle,
            env=dict(self.env,**env),capture_output=True,text=True,timeout=20)
        assert (p.returncode==0)==ok,(action,p.returncode,p.stdout,p.stderr)
        assert 'ACTUATOR' not in (self.r/'operations').read_text()
        return p
    def helper(self,*args,ok=True):
        text=(self.old/'scripts/seat-action.sh').read_text()
        text=text.replace(PREFIX,'export PATH='+self.env['PATH']).replace('/data/nemesis',str(self.data))
        text=text.replace('/dev/seat-comfort',str(self.r/'dev/seat-comfort'))
        p=subprocess.run(['sh','-c',text,'helper',*args],env=self.env,capture_output=True,text=True)
        assert (p.returncode==0)==ok,(p.stdout,p.stderr)
        return p
    def migrate(self,**kw): return self.run('migrate','APPROVE-MIGRATION',**kw)
    def recover(self,**kw): return self.run('recover','APPROVE-RECOVERY',**kw)
@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as folder: yield Fixture(folder)
with fixture() as f:
    before=tree(f.data)
    assert 'PREFLIGHT PASS' in f.run().stdout
    f.run('migrate',ok=False)
    assert tree(f.data)==before and not f.back.exists()
print('PASS default preflight and missing token preserve installation')
for case in ['firmware','android-down','apk','descriptor','extra-service','link','lock','existing-backup']:
    with fixture() as f:
        env={}
        if case=='firmware': env['BUILD']='wrong'
        elif case=='android-down': env['BOOT']='0'
        elif case=='apk': (f.r/'installed.apk').write_bytes(b'wrong')
        elif case=='descriptor': (f.old/'NEMESIS.data').write_text('preuninstall=unknown.sh\n')
        elif case=='extra-service': env['EXTRA_SERVICE']='1'
        elif case=='link': (f.state/'symlink').symlink_to(f.r/'installed.apk')
        elif case=='lock': f.lock.mkdir(parents=True)
        elif case=='existing-backup': f.back.mkdir(parents=True)
        f.migrate(ok=False,**env)
        assert 'uninstall coldstart.heat' not in (f.r/'operations').read_text()
print('PASS firmware, Android, APK, hooks, service, symlink, lock and snapshot gates')
with fixture() as f:
    f.migrate()
    assert tree(f.state)==f.before==tree(f.back/'state')==tree(f.back/'state-check')
    assert (f.back/'HOLD').exists()
    assert json.loads((f.r/'registry.json').read_text())==['auto-seat']
    assert not (f.old/'NEMESIS.data').exists()
    assert 'CONFIG_READ' in f.helper('read').stdout
    f.helper('driver_heat','3',ok=False)
    f.helper('save','1','50','1','3','3','0','0','75','0','0','0',ok=False)
    startup=(f.new/'svc/auto-seat.sh').read_text().replace(PREFIX,'export PATH='+f.env['PATH'])
    startup=startup.replace('/data/nemesis',str(f.data))
    p=subprocess.run(['sh','-c',startup],env=f.env,capture_output=True,text=True,timeout=5)
    assert p.returncode==0 and 'migration hold' in p.stdout.lower()
    assert 'ACTUATOR' not in (f.r/'operations').read_text()
    f.run('accept',ok=False); f.run('accept','APPROVE-ACCEPTANCE')
    assert not (f.back/'HOLD').exists()
    f.recover()
    assert json.loads((f.r/'registry.json').read_text())==['coldstart.heat']
    assert tree(f.state)==f.before and tree(f.old)==tree(f.bundle/'original')
    assert (f.back/'RECOVERED').exists()
    f.run('accept','APPROVE-ACCEPTANCE',ok=False)
print('PASS migration, opaque settings, bridge read, blocked control/save/startup, acceptance, recovery')
for failure in ['backup','uninstall','install','postinstall']:
    with fixture() as f:
        f.migrate(ok=False,FAIL=failure)
        assert not f.lock.exists()
        if failure=='backup':
            assert not (f.back/'READY').exists()
            f.recover(ok=False)
            assert f.old.exists() and tree(f.state)==f.before
        else:
            assert (f.back/'HOLD').exists()
            f.recover()
            assert tree(f.state)==f.before and f.old.exists() and not f.new.exists()
print('PASS backup/uninstall/install failure recovery')
with fixture() as f:
    f.migrate(ok=False,FAIL='install')
    f.recover(ok=False,FAIL='recover-install')
    assert (f.back/'HOLD').exists() and (f.back/'READY').exists()
    f.recover(); assert tree(f.state)==f.before
print('PASS failed recovery can be retried without replacing snapshot')
with fixture() as f:
    f.migrate(); (f.back/'state-check/threshold_f').write_text('corrupt')
    f.recover(ok=False); assert f.new.exists() and (f.back/'HOLD').exists()
print('PASS corrupt backup refuses removal')
with fixture() as f:
    f.migrate(ok=False,FAIL='install')
    f.old.mkdir(); (f.old/'unknown').write_text('never remove')
    f.recover(ok=False); assert (f.old/'unknown').read_text()=='never remove'
print('PASS unknown orphan retained')
with fixture() as f:
    f.migrate(); shutil.rmtree(f.r/'dev'); f.recover()
    assert tree(f.state)==f.before
print('PASS recovery after simulated reboot')

with fixture() as f:
    # Missing original setting keys must remain absent after migration and recovery.
    (f.state/'threshold_f').unlink(); (f.state/'cool_enabled').unlink()
    f.before=tree(f.state)
    f.migrate(); assert tree(f.state)==f.before
    f.recover(); assert tree(f.state)==f.before
print('PASS absent setting files survive both new and original postinstall defaults')

with fixture() as f:
    f.migrate()
    (f.old/'scripts/seat-action.sh').write_bytes(b'partial interrupted copy')
    f.recover()
    assert tree(f.old)==tree(f.bundle/'original')
print('PASS owned partial bridge copy can be removed during recovery')

with fixture() as f:
    f.migrate(); (f.old/'unknown').write_text('retain')
    before=tree(f.old)
    f.recover(ok=False)
    assert tree(f.old)==before and (f.back/'HOLD').exists()
print('PASS unknown bridge contents fail without partial cleanup')
