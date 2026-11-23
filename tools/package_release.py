"""Reproduce the clean autoseat.heat release; no keys, app rebuild or migration."""
from pathlib import Path
import argparse, configparser, hashlib, io, json, os, shutil, subprocess, tempfile, zipfile

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'release.json').read_text())
APK_SHA='97a181a2289ac31285d8347964dfeba7e6982da7447968886dc53d5302b7ad3b'
RELEASE_SHA='32d6e014421bc2ff1104de3c004079377c39b8e62eae0e1c6f2d470e9aefb5ad'
CERT_SHA='6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59'
sha=lambda data:hashlib.sha256(data).hexdigest()

def pack(files,out):
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            assert '\\' not in name and not name.startswith('/') and '..' not in name.split('/')
            info=zipfile.ZipInfo(name,(2026,11,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
            z.writestr(info,data)
    with zipfile.ZipFile(out) as z:assert z.testzip() is None

def build(verify_signature=False, startup_candidate=False):
    original=ROOT/'downloads/Ioniq5-auto-seat-2.0.zip'
    assert sha(original.read_bytes())==RELEASE_SHA,'Original immutable release changed'
    with zipfile.ZipFile(original) as z:apk=z.read('app/auto-seat.apk')
    assert sha(apk)==APK_SHA
    with zipfile.ZipFile(io.BytesIO(apk)) as z:assert z.read('classes.dex')[:8]==b'dex\n035\0'
    signature='not rerun (immutable original APK byte identity checked)'
    if verify_signature:
        sdk=os.environ.get('ANDROID_SDK') or os.environ.get('ANDROID_HOME')
        assert sdk,'ANDROID_HOME or ANDROID_SDK required for signature verification'
        signer=Path(sdk)/'build-tools/30.0.3/apksigner'
        assert signer.is_file(),signer
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'original.apk';p.write_bytes(apk)
            checked=subprocess.run([str(signer),'verify','--verbose','--min-sdk-version','19','--print-certs',str(p)],check=True,capture_output=True,text=True)
            assert 'Verified using v1 scheme (JAR signing): true' in checked.stdout
            assert 'Signer #1 certificate SHA-256 digest: '+CERT_SHA in checked.stdout
        signature='expected signer, KitKat v1 signature and DEX 035 verified'
    package={p.relative_to(ROOT/'package').as_posix():p.read_bytes() for p in (ROOT/'package').rglob('*') if p.is_file() and p.name not in ['desktop.ini','Thumbs.db']}
    package['app/auto-seat.apk']=apk
    for name in ['LICENSE','CREDITS.md']:package[name]=(ROOT/name).read_bytes()
    metadata=configparser.ConfigParser(interpolation=None);metadata.read_string(package['NEMESIS.data'].decode())
    assert metadata['nemesis']['id']==CONFIG['package_id']=='autoseat.heat'
    assert metadata['nemesis']['package-version']==CONFIG['version']=='2.0'
    for section in metadata.sections():
        for key,value in metadata[section].items():
            assert all(len(x)<64 for x in (value.split(',') if key=='depends' else [value])),(section,key)
    for key in ['preinstall','postinstall','preuninstall']:assert metadata['nemesis'][key] in package
    for section in ['app.0','service.0']:assert metadata[section]['path'] in package
    usb={p.relative_to(ROOT/'usb').as_posix():p.read_bytes() for p in (ROOT/'usb').rglob('*') if p.is_file()}
    inventory=json.loads((ROOT/'verification/vehicle-tested-runtime-sha256.json').read_text())
    changed_runtime=[]
    for path,want in inventory.items():
        folder,name=path.split('/',1)
        if sha((package if folder=='package' else usb)[name])!=want:
            changed_runtime.append(path)
    if startup_candidate:
        assert changed_runtime==['package/svc/auto-seat.sh'],('Unexpected candidate runtime changes',changed_runtime)
    else:
        assert not changed_runtime,'Vehicle-tested runtime drift: '+','.join(changed_runtime)
    assert all(b'auto-seat-migration-v1/HOLD' not in data for name,data in package.items() if name.endswith('.sh'))
    out=ROOT/('dist/startup-candidate' if startup_candidate else 'dist');out.mkdir(parents=True,exist_ok=True)
    inner=out/'autoseat.heat-2.0.zip';pack(package,inner)
    usb['autoseat.heat-2.0.zip']=inner.read_bytes()
    usb['LICENSE']=(ROOT/'LICENSE').read_bytes();usb['CREDITS.md']=(ROOT/'CREDITS.md').read_bytes()
    suffix='-startup-fix-RC2' if startup_candidate else ''
    if startup_candidate:
        usb['READ-ME.txt']=(ROOT/'docs/STARTUP-TEMPERATURE-CANDIDATE.md').read_bytes()
    outer=out/('Auto-Seat-2.0-autoseat.heat'+suffix+'-USB.zip');pack(usb,outer)
    source={}
    for directory in ['app/src','app/res','package/scripts','package/svc','tests','tools','artwork','docs','usb','verification','.github']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and 'target' not in p.parts:
                source['auto-seat/'+p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for p in ROOT.iterdir():
        if p.is_file() and (p.suffix in ['.md','.txt'] or p.name in ['LICENSE','.gitignore','release.json']):source['auto-seat/'+p.name]=p.read_bytes()
    for name in ['app/AndroidManifest.xml','package/NEMESIS.data','downloads/Ioniq5-auto-seat-2.0.zip']:
        source['auto-seat/'+name]=(ROOT/name).read_bytes()
    src=out/('Auto-Seat-2.0-autoseat.heat'+suffix+'-source.zip');pack(source,src)
    report={'package_id':CONFIG['package_id'],'version':CONFIG['version'],'original_apk_sha256':APK_SHA,'apk_signature_check':signature,'vehicle_tested_runtime_files_match':True,'on_vehicle_evidence':'clean install verified and owner reports working operation on one US 2023 IONIQ 5 Limited Gen5W; other vehicles unverified','human_code_review':False,'build_commit':os.environ.get('GITHUB_SHA','local build')}
    if startup_candidate:
        report.update(candidate=True,candidate_revision=2,vehicle_tested_runtime_files_match=False,
                      changed_runtime_files=changed_runtime,
                      on_vehicle_evidence='RC2 action confirmation/live capture/delayed retry have NOT been tested on a vehicle; host simulations only.',
                      original_apk_unchanged=True)
    record=out/'build-validation.json';record.write_text(json.dumps(report,indent=2)+'\n')
    checksums=out/'SHA256SUMS.txt';checksums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in [outer,inner,src,record]),newline='\n')
    print(json.dumps(report,indent=2));return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-signature',action='store_true')
    parser.add_argument('--startup-candidate',action='store_true',help='Build only the explicitly unvalidated service-fix candidate')
    args=parser.parse_args();build(args.verify_signature,args.startup_candidate)
