"""Inspect generated archives independently of the packager."""
from pathlib import Path
import hashlib, io, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
def digest(b): return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(ROOT/'downloads/Ioniq5-auto-seat-2.0.zip') as z:
    original=z.read('app/auto-seat.apk')
assert digest(original)=='97a181a2289ac31285d8347964dfeba7e6982da7447968886dc53d5302b7ad3b'
with zipfile.ZipFile(io.BytesIO(original)) as a:
    assert a.read('classes.dex')[:8]==b'dex\n035\x00'
    assert b'/data/nemesis/apps/coldstart.heat/scripts/seat-action.sh' in a.read('classes.dex')
inner=OUT/'Ioniq5-auto-seat-2.0-MIGRATION-UNTESTED.zip'
with zipfile.ZipFile(inner) as z:
    assert z.read('app/auto-seat.apk')==original
    names=z.namelist()
    assert len(names)==len(set(names)) and 'NEMESIS.data' in names
    assert all(not n.startswith('/') and '..' not in n.split('/') for n in names)
    d=z.read('NEMESIS.data').decode()
    assert 'id=auto-seat\n' in d and 'depends=!coldstart.heat\n' in d
    assert 'package=com.nemesis.coldstart\n' in d and 'preuninstall=scripts/preun.sh\n' in d
    for n in ['scripts/bridge.sh','scripts/preun.sh','scripts/seat-action.sh','svc/auto-seat.sh']:
        assert z.read(n)==(ROOT/'package'/n).read_bytes()
with zipfile.ZipFile(OUT/'Ioniq5-auto-seat-2.0-PREFLIGHT-USB.zip') as kit:
    assert 'type=execute\npath=actions/check.sh\n' in kit.read('NEMESIS.data').decode()
    assert b'migrate.sh check\n' in kit.read('actions/check.sh')
    assert 'NEMESIS.emergency' not in kit.namelist()
    assert kit.read('candidate.zip')==inner.read_bytes()
    assert kit.read('original.zip')==(ROOT/'downloads/Ioniq5-auto-seat-2.0.zip').read_bytes()
    assert kit.read('original/app/auto-seat.apk')==original
    with zipfile.ZipFile(io.BytesIO(kit.read('candidate.zip'))) as z:
        for n in z.namelist(): assert z.read(n)==kit.read('candidate/'+n)
    assert kit.read('migrate.sh')==(ROOT/'migration/migrate.sh').read_bytes()
    for action in ['MIGRATE','RECOVER','ACCEPT']:
        assert b'type=execute' in kit.read('actions/'+action+'.data')
    for n in ['VEHICLE-TEST.md','STORE-MIGRATION.md','STORE-SUBMISSION.md']:
        assert kit.read(n)==(ROOT/n).read_bytes()
with zipfile.ZipFile(OUT/'Ioniq5-auto-seat-2.0-source.zip') as z:
    for n in ['migration/migrate.sh','STORE-MIGRATION.md','VEHICLE-TEST.md','STORE-SUBMISSION.md','tests/check_migration.py']:
        assert z.read('auto-seat/'+n)==(ROOT/n).read_bytes()
    assert not any(n.endswith(('.jks','.keystore','.pem','.key','.apk')) for n in z.namelist())
assert b'\\n' not in (OUT/'READ-ME.txt').read_bytes()
# Review USB opens Manager; only the dedicated preflight kit executes a check.
assert 'type=open\n' in (OUT/'NEMESIS.data').read_text()
for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split('  ',1)
    assert digest((OUT/name).read_bytes())==expected
print('PASS nested archive layouts, preflight default, original APK/DEX/helper path, source/docs, checksums and secret exclusion')
