#!/usr/bin/env python3
"""Idempotent: xmllint (build) rejects Qualcomm data xmls whose <?xml?> declaration follows a leading comment. Move the declaration first."""
import pathlib, re
d = pathlib.Path.home() / 'kyf37-android10/vendor/kyocera/kyf37/proprietary/etc/data'
for f in sorted(d.glob('*.xml')):
    t = f.read_text(encoding='utf-8')
    m = re.search(r'<\?xml[^>]*\?>[ \t]*\r?\n?', t)
    if m and m.start() > 0:
        t = m.group(0).rstrip() + '\n' + t[:m.start()] + t[m.end():]
        f.write_text(t, encoding='utf-8'); print('fixed', f.name)
