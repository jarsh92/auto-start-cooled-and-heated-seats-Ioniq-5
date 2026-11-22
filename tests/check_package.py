"""Check public archives, attribution and owner-tested runtime identity."""
from pathlib import Path
import configparser, hashlib, io, json, sys, zipfile

ROOT=Path(__file__).resolve().parents[1];out=ROOT/'dist'
candidate='--startup-candidate' in sys.argv
suffix='-startup-fix-CANDIDATE' if candidate else ''
if candidate:out=out/'startup-candidate'
with zipfile.ZipFile(out/('Auto-Seat-2.0-autoseat.heat'+suffix+'-USB.zip')) as usb:
    assert usb.testzip() is None
    assert usb.read('NEMESIS.data')==b'[nemesis]\nversion=1.0\ntype=execute\npath=NEMESIS.sh\n'
    assert b'./clean-install.sh' in usb.read('NEMESIS.sh')
    with zipfile.ZipFile(io.BytesIO(usb.read('autoseat.heat-2.0.zip'))) as pkg:
        assert pkg.testzip() is None
        m=configparser.ConfigParser(interpolation=None);m.read_string(pkg.read('NEMESIS.data').decode())
        assert m['nemesis']['id']=='autoseat.heat' and m['nemesis']['depends']=='!coldstart.heat,!auto-seat'
        changed=[]
        for name,want in json.loads((ROOT/'verification/vehicle-tested-runtime-sha256.json').read_text()).items():
            folder,path=name.split('/',1)
            if hashlib.sha256((pkg if folder=='package' else usb).read(path)).hexdigest()!=want:changed.append(name)
        assert changed==(['package/svc/auto-seat.sh'] if candidate else []),changed
        assert b'No independent human code review' in pkg.read('CREDITS.md')
    assert (b'NOT YET VEHICLE-TESTED' if candidate else b'AI-WRITTEN') in usb.read('READ-ME.txt')
with zipfile.ZipFile(out/('Auto-Seat-2.0-autoseat.heat'+suffix+'-source.zip')) as z:
    assert z.testzip() is None
    for name in z.namelist():
        assert not name.startswith('/') and '..' not in name.split('/')
        assert not name.lower().endswith(('.jks','.keystore','.log','.env'))
        assert 'vehicle-logs' not in name and 'private-signing' not in name
    assert 'auto-seat/migration/migrate.sh' not in z.namelist()
    for name in ['README.md','CREDITS.md','RELEASE-NOTES.md','EXTENDING.md','STORE-SUBMISSION.md']:
        text=z.read('auto-seat/'+name).decode()
        assert 'ChatGPT' in text and 'human' in text
        assert text.rstrip().endswith('This post was prepared and posted with ChatGPT.')
if candidate:
    report=json.loads((out/'build-validation.json').read_text())
    assert report['candidate'] and not report['vehicle_tested_runtime_files_match']
    assert report['original_apk_unchanged']
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
    want,name=line.split('  ',1);assert hashlib.sha256((out/name).read_bytes()).hexdigest()==want
print('PASS package/source/USB/checksums/runtime scope and public attribution; no private logs/keys. Candidate:',candidate)
