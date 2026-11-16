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
apk = ROOT / 'app/auto-seat.apk'
if not apk.is_file():
    raise SystemExit('Build the signed app/auto-seat.apk first.')
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
for directory in ['app/src', 'app/res', 'package/scripts', 'package/svc', 'tests', 'tools', 'artwork']:
    for p in (ROOT / directory).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and 'target' not in p.parts:
            source_files.append((p, 'auto-seat/' + p.relative_to(ROOT).as_posix()))
for name in ['.gitignore', 'app/AndroidManifest.xml', 'package/NEMESIS.data', 'LICENSE', 'CREDITS.md', 'README.md', 'UPSTREAM-README.md', 'EXTENDING.md', 'UPDATE-2.0.md', 'VALIDATION-2.0.md', 'COMPATIBILITY.txt']:
    source_files.append((ROOT / name, 'auto-seat/' + name))
source = out / ('Ioniq5-auto-seat-' + version + '-source.zip')
write_zip(source, source_files)
descriptor = out / 'NEMESIS.data'
descriptor.write_text('[nemesis]\nversion=1.0\ntype=install\npath=' + inner.name + '\n')
readme = out / 'READ-ME.txt'
readme.write_text(
    'AUTO SEAT ' + version + ' — UNTESTED MIGRATION CANDIDATE\\n\\n'
    'DO NOT INSTALL ON A VEHICLE OR SUBMIT TO THE NEMESIS STORE.\\n'
    'This candidate uses the new auto-seat package ID, which conflicts with\\n'
    'the previously installed coldstart.heat package. Same-ID update instructions\\n'
    'do not apply. A supported, backup-verified migration and recovery procedure\\n'
    'must be developed and tested before the old package is removed.\\n\\n'
    'The firmware guard requires eng.vmadmin.20260903.161833.\\n'
    'Compatibility beyond the owner-tested US 2023 Ioniq 5 Gen5W is unverified.\\n'
    'See STORE-MIGRATION.md in the GitHub source for migration requirements.\\n'
)

usb = out / ('Ioniq5-auto-seat-' + version + '-MIGRATION-UNTESTED-USB.zip')
write_zip(usb, [(descriptor, 'NEMESIS.data'), (inner, inner.name), (readme, 'READ-ME.txt'), (source, 'source/' + source.name), (ROOT / 'LICENSE', 'LICENSE'), (ROOT / 'CREDITS.md', 'CREDITS.md'), (ROOT / 'COMPATIBILITY.txt', 'COMPATIBILITY.txt'), (ROOT / 'README.md', 'README.md')])
checksums = out / 'SHA256SUMS.txt'
checksums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in [inner, source, usb]))
for p in [inner, source, usb, checksums]:
    print(p)
