"""Inspect the historical Actions artifact and immutable original release."""
from pathlib import Path
import hashlib, io, json, os, urllib.request, zipfile
ROOT = Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
release = ROOT / 'downloads/Ioniq5-auto-seat-2.0.zip'
assert sha(release.read_bytes()) == '32d6e014421bc2ff1104de3c004079377c39b8e62eae0e1c6f2d470e9aefb5ad'
with zipfile.ZipFile(release) as z:
    print('ORIGINAL CONTENTS', z.namelist())
    print('ORIGINAL DESCRIPTOR\n' + z.read('NEMESIS.data').decode())
    for name in z.namelist():
        if name.endswith('.sh'): print('ORIGINAL SCRIPT', name, sha(z.read(name)))
    original_apk = z.read('app/auto-seat.apk')
assert sha(original_apk) == '97a181a2289ac31285d8347964dfeba7e6982da7447968886dc53d5302b7ad3b'
# GitHub token is used only in the Authorization header, never printed.
url = 'https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/actions/artifacts/14281222235/zip'
req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept':'application/vnd.github+json'})
class ArtifactRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected:
            redirected.remove_header('Authorization')
        return redirected
with urllib.request.build_opener(ArtifactRedirect).open(req, timeout=60) as r:
    archive = r.read()
assert sha(archive) == '213151f7eb95b483baa34cd076ff9d44e2a778c145f4ea93cb039ac6918cabd0'
with zipfile.ZipFile(io.BytesIO(archive)) as outer:
    print('HISTORICAL ARTIFACT CONTENTS', outer.namelist())
    name = 'Ioniq5-auto-seat-2.0-MIGRATION-UNTESTED.zip'
    with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
        print('HISTORICAL INNER CONTENTS', inner.namelist())
        assert inner.read('app/auto-seat.apk') == original_apk
        print('HISTORICAL DESCRIPTOR\n' + inner.read('NEMESIS.data').decode())
    print('HISTORICAL README', repr(outer.read('READ-ME.txt').decode()))
print('PASS historical artifact digest, nested ZIP, original APK byte identity')
