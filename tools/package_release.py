"""Package the approved release inputs; never scan parent folders for files."""
from pathlib import Path
import hashlib
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://schemas.android.com/apk/res/android}'
version = ET.parse(ROOT / 'app/AndroidManifest.xml').getroot().get(NS + 'versionName')
assert version and all(c.isdigit() or c == '.' for c in version)
# Reuse the owner-tested, originally signed APK from the published release.
# Never rebuild, re-sign, or silently substitute an APK for this store candidate.
RELEASE = ROOT / 'downloads/Ioniq5-auto-seat-2.0.zip'
RELEASE_SHA256 = '32d6e014421bc2ff1104de3c004079377c39b8e62eae0e1c6f2d470e9aefb5ad'
EXPECTED_CERT = '6b555bd8920206e9588aaa68a63ed94ffdbebe68ad3a4c909b7d4ebb877bab59'
if hashlib.sha256(RELEASE.read_bytes()).hexdigest() != RELEASE_SHA256:
    raise SystemExit('Original release archive checksum mismatch; refusing to package.')
with zipfile.ZipFile(RELEASE) as old:
    apk_entries = [n for n in old.namelist() if n.endswith('.apk') and not n.endswith('/')]
    if len(apk_entries) != 1:
        raise SystemExit(f'Expected exactly one APK in original release; found {apk_entries!r}')
    original_apk = old.read(apk_entries[0])
    original_files = {n: old.read(n) for n in old.namelist() if not n.endswith('/')}
# Verify the original signature using Android SDK apksigner, without requiring any key.
import os
import subprocess
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    temp_apk = Path(tmp) / 'original.apk'
    temp_apk.write_bytes(original_apk)
    sdk = os.environ.get('ANDROID_SDK') or os.environ.get('ANDROID_HOME')
    if not sdk:
        raise SystemExit('ANDROID_SDK or ANDROID_HOME is required for signature verification.')
    apksigner = Path(sdk) / 'build-tools/30.0.3/apksigner'
    if not apksigner.is_file():
        raise SystemExit(f'Cannot find Android apksigner at {apksigner}')
    check = subprocess.run([str(apksigner), 'verify', '--verbose', '--min-sdk-version', '19', '--print-certs', str(temp_apk)],
                           capture_output=True, text=True)
    if check.returncode:
        raise SystemExit('Original APK signature verification failed: ' + check.stderr)
    if 'Verified using v1 scheme (JAR signing): true' not in check.stdout:
        raise SystemExit('KitKat v1 signature verification is required.')
    certs = [line.split(':', 1)[1].strip().lower().replace(':', '')
             for line in check.stdout.splitlines()
             if line.startswith('Signer #1 certificate SHA-256 digest:')]
    if certs != [EXPECTED_CERT]:
        raise SystemExit('Original APK signing certificate does not match the owner-tested build.')
    apk = ROOT / 'app/auto-seat.apk'
    apk.write_bytes(original_apk)
package = ROOT / 'package'
(package / 'app').mkdir(exist_ok=True)
shutil.copyfile(apk, package / 'app/auto-seat.apk')
for name in ['LICENSE', 'CREDITS.md']:
    shutil.copyfile(ROOT / name, package / name)
out = ROOT / 'dist'
out.mkdir(exist_ok=True)

def write_zip(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for file, name in sorted(files, key=lambda x: x[1]):
            entry = zipfile.ZipInfo(name, date_time=(2026, 11, 13, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            z.writestr(entry, file.read_bytes())

inner = out / ('Ioniq5-auto-seat-' + version + '-MIGRATION-UNTESTED.zip')
write_zip(inner, [(p, p.relative_to(package).as_posix()) for p in package.rglob('*') if p.is_file()])
# Public source allowlist: no keys, access files, local toolchains, or private backups.
source_files = []
for directory in ['app/src', 'app/res', 'package/scripts', 'package/svc', 'tests', 'tools', 'artwork', 'migration']:
    for p in (ROOT / directory).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and 'target' not in p.parts:
            source_files.append((p, 'auto-seat/' + p.relative_to(ROOT).as_posix()))
for name in ['.gitignore', 'app/AndroidManifest.xml', 'package/NEMESIS.data', 'LICENSE', 'CREDITS.md', 'README.md', 'UPSTREAM-README.md', 'EXTENDING.md', 'UPDATE-2.0.md', 'VALIDATION-2.0.md', 'COMPATIBILITY.txt', 'STORE-MIGRATION.md', 'VEHICLE-TEST.md', 'STORE-SUBMISSION.md', 'MIGRATION-VALIDATION.md', '.github/workflows/auto-seat-ci.yml', 'downloads/Ioniq5-auto-seat-2.0.zip']:
    source_files.append((ROOT / name, 'auto-seat/' + name))
source = out / ('Ioniq5-auto-seat-' + version + '-source.zip')
write_zip(source, source_files)
descriptor = out / 'NEMESIS.data'
descriptor.write_text('[nemesis]\nversion=1.0\ntype=open\n')
readme = out / 'READ-ME.txt'
readme.write_text(
    'AUTO SEAT ' + version + ' — UNTESTED MIGRATION CANDIDATE\n\n'
    'DO NOT INSTALL ON A VEHICLE OR SUBMIT TO THE NEMESIS STORE.\n'
    'This candidate uses the new auto-seat package ID, which conflicts with\n'
    'the previously installed coldstart.heat package. Same-ID update instructions\n'
    'do not apply. A supported, backup-verified migration and recovery procedure\n'
    'is supplied separately as a preflight-first migration kit.\n\n'
    'The firmware guard requires eng.vmadmin.20260903.161833.\n'
    'Compatibility beyond the owner-tested US 2023 Ioniq 5 Gen5W is unverified.\n'
    'See STORE-MIGRATION.md in the GitHub source for migration requirements.\n'
)

usb = out / ('Ioniq5-auto-seat-' + version + '-MIGRATION-UNTESTED-USB.zip')
write_zip(usb, [(descriptor, 'NEMESIS.data'), (inner, inner.name), (readme, 'READ-ME.txt'), (source, 'source/' + source.name), (ROOT / 'LICENSE', 'LICENSE'), (ROOT / 'CREDITS.md', 'CREDITS.md'), (ROOT / 'COMPATIBILITY.txt', 'COMPATIBILITY.txt'), (ROOT / 'README.md', 'README.md')])

# Separate execute kit defaults to a read-only check. Never auto-install this ZIP.
kit = out / 'migration-kit'
if kit.exists(): shutil.rmtree(kit)
kit.mkdir()
(kit / 'original').mkdir()
for name, data in original_files.items():
    target = kit / 'original' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
shutil.copyfile(RELEASE, kit / 'original.zip')
shutil.copyfile(inner, kit / 'candidate.zip')
shutil.copytree(package, kit / 'candidate')
shutil.copyfile(ROOT / 'migration/migrate.sh', kit / 'migrate.sh')
(kit / 'actions').mkdir()
for action, token in [('check', ''), ('migrate', ' APPROVE-MIGRATION'),
                      ('recover', ' APPROVE-RECOVERY'), ('accept', ' APPROVE-ACCEPTANCE')]:
    (kit / 'actions' / (action + '.sh')).write_text(
        '#!/system/bin/sh\nexec /system/bin/sh ./migrate.sh ' + action + token + '\n')
    (kit / 'actions' / (action.upper() + '.data')).write_text(
        '[nemesis]\nversion=1.0\ntype=execute\npath=actions/' + action + '.sh\n')
shutil.copyfile(kit / 'actions/CHECK.data', kit / 'NEMESIS.data')
for name in ['VEHICLE-TEST.md', 'STORE-MIGRATION.md', 'STORE-SUBMISSION.md', 'MIGRATION-VALIDATION.md', 'LICENSE', 'CREDITS.md']:
    shutil.copyfile(ROOT / name, kit / name)
migration_usb = out / ('Ioniq5-auto-seat-' + version + '-PREFLIGHT-USB.zip')
write_zip(migration_usb, [(p, p.relative_to(kit).as_posix()) for p in kit.rglob('*') if p.is_file()])
shutil.rmtree(kit)
checksums = out / 'SHA256SUMS.txt'

checksums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in [inner, source, usb, migration_usb]))
for p in [inner, source, usb, migration_usb, checksums]:
    print(p)
