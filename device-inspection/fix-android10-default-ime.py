#!/usr/bin/env python3
"""Idempotent: make TT9 (io.github.sspanak.tt9) the default keyboard on a fresh or data-reset ROM.
Android 10's SettingsProvider has no default-input-method resource, so IMMS picks LatinIME (its touch keyboard swallows
Up/Down in text fields on this non-touch phone; found 2026-10-10). A one-shot init service runs once per user-data lifetime
(guard property persist.kyf37.ime_default_done) and sets TT9 as default. User changes made afterwards are never overridden.
Stages: vendor/kyocera/kyf37/proprietary/ime/{kyf37-default-ime.sh,init.kyf37.ime.rc} + PRODUCT_COPY_FILES (system/etc).
Run in WSL when no build is running."""
import pathlib, shutil
T = pathlib.Path.home() / 'kyf37-android10'
ven = T / 'vendor/kyocera/kyf37'
d = ven / 'proprietary/ime'
d.mkdir(parents=True, exist_ok=True)
NL = chr(10)
script = NL.join([
    '#!/system/bin/sh',
    '# Set TT9 as the default keyboard once (first boot after install or data reset).',
    '[ "$(getprop persist.kyf37.ime_default_done)" = 1 ] && exit 0',
    'IME=io.github.sspanak.tt9/.ime.TraditionalT9',
    'i=0; while [ $i -lt 30 ]; do',
    '  /system/bin/ime list -s 2>/dev/null | grep -q "$IME" && break',
    '  i=$((i+1)); sleep 2',
    'done',
    '/system/bin/ime enable "$IME" >/dev/null 2>&1',
    '/system/bin/ime set "$IME" >/dev/null 2>&1',
    '[ "$(/system/bin/settings get secure default_input_method)" = "$IME" ] && setprop persist.kyf37.ime_default_done 1',
    ''])
rc = NL.join([
    '# One-shot default keyboard (TT9). See fix-android10-default-ime.py',
    'service kyf37-default-ime /system/bin/sh /system/etc/kyf37-default-ime.sh',
    '    class main',
    '    user root',
    '    group root',
    '    seclabel u:r:init:s0',
    '    disabled',
    '    oneshot',
    '',
    'on property:sys.boot_completed=1',
    '    start kyf37-default-ime',
    ''])
for name, text in (('kyf37-default-ime.sh', script), ('init.kyf37.ime.rc', rc)):
    f = d / name
    if not f.exists() or f.read_text() != text:
        f.write_text(text, newline=NL); print('wrote', f)
mk = ven / 'kyf37-vendor.mk'
t = mk.read_text()
rules = ['vendor/kyocera/kyf37/proprietary/ime/kyf37-default-ime.sh:system/etc/kyf37-default-ime.sh',
         'vendor/kyocera/kyf37/proprietary/ime/init.kyf37.ime.rc:system/etc/init/init.kyf37.ime.rc']
add = [r for r in rules if r not in t]
if add:
    mk.write_text(t.rstrip(NL) + NL + ''.join('PRODUCT_COPY_FILES += %s%s' % (r, NL) for r in add)); print('copy rules added:', len(add))
else:
    print('copy rules present')
print('done')
