"""Generate a boot-only completion path from the checked v23 installer.

Requires exact live system readback before writing boot. Original rollback is
retained. All model, geometry, owner keystore, helper and protected checks remain.
"""
from pathlib import Path
import json, re, zipfile, hashlib
root=Path(__file__).resolve().parent.parent
release=json.loads((root/'kyf37-rom/v23-validation.json').read_text())
zpath=Path(release['zip'])
assert hashlib.sha256(zpath.read_bytes()).hexdigest()==release['sha256']
with zipfile.ZipFile(zpath) as z:
    s=z.read('META-INF/com/google/android/update-binary').decode()
    manifest=json.loads(z.read('payload-manifest.json'))
assert 'RECOVERY_HASH=c7f5a41565595607a10930ddb174f9755568c01156a6440c34abdb5cca25141d' in s
assert 'SYSTEM_HASH='+manifest['system.raw.img']['sha256'] in s
assert 'BOOT_HASH='+manifest['boot.img']['sha256'] in s
line='[ "$(payload_hash system.raw.img)" = "$SYSTEM_HASH" ] || die \'System payload is damaged.\''
assert line in s
s=s.replace(line, '# Live system is verified below instead of rewriting it.')
start=s.index('BACKUP=$SD/KYF37-Android10-rollback-')
end=s.index('# Record unchanged protected/radio partition hashes',start)
s=s[:start]+'''BACKUP=$SD/KYF37-Android10-rollback-20171201-125359-301
[ -s "$BACKUP/boot.img" ] && [ -s "$BACKUP/system.img" ] || die 'Original rollback pair missing.'
[ -f "$BACKUP/SHA256SUMS" ] || die 'Original rollback manifest missing.'
$BB grep -q '^a6cfffd384a196cabf9eb328c99cd91fe760a7e4fe6355e9dce02e98eb54170e  boot.img$' "$BACKUP/SHA256SUMS" || die 'Rollback boot manifest differs.'
$BB grep -q '^4f76ad5442b945ab1e86a8384298b029df0c794ff704f606efabc00df0ab9913  system.img$' "$BACKUP/SHA256SUMS" || die 'Rollback system manifest differs.'
ui 'Verifying existing system readback; no system write will be performed...'
check "$BLOCK/system" "$SYSTEM_HASH"
ui 'Existing system matches the validated v23 image.'
'''+s[end:]
line='"$WORK/clear-system-temp-wp" --clear-system-temporary || die \'System temporary write-protection check failed.\''
assert line in s
s=s.replace(line,'# System remains untouched in completion mode.')
start=s.index("ui 'Writing system image...'")
end=s.index("ui 'Writing owner-signed boot image...'",start)
s=s[:start]+s[end:]
assert 'of="$BLOCK/system"' not in s
assert 'of="$BLOCK/boot"' in s
assert 'check "$BLOCK/system" "$SYSTEM_HASH"' in s
assert 'check "$BLOCK/boot" "$BOOT_HASH"' in s
assert 'while read expected part; do check "$BLOCK/$part" "$expected"; done' in s
dest=root/'device-inspection/v23-resume-verified-system.sh'
dest.write_text(s,newline='\n')
print(dest)
