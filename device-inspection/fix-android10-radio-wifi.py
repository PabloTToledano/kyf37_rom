#!/usr/bin/env python3
"""Wi-Fi fixes found by the radio agent (2026-10-08). Idempotent. Run in WSL:

    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-radio-wifi.py

Root cause fixed (verified live on the phone, see RADIO.md section 2):
  wpa_supplicant enabled P2P on the STA interface wlan0 (the driver is P2P capable), so the HIDL object for wlan0
  was registered as ISupplicantP2pIface and ISupplicant.addInterface(STA) returned FAILURE_UNKNOWN
  ("Failed to create ISupplicantIface 1"), and Wi-Fi never turned on.  The standard Qualcomm/CAF fix is
  `p2p_disabled=1` in the STA overlay (P2P lives on p2p0 via the P2P conf).

What this script does:
  1. writes device/kyocera/kyf37/radio/{wpa_supplicant.conf,wpa_supplicant_overlay.conf,p2p_supplicant_overlay.conf}
  2. installs them to /vendor/etc/wifi (system/vendor/etc/wifi in this tree) via PRODUCT_COPY_FILES.  The files were
     only ever pushed live; no build rule installed them.  Earlier rules for the same destinations are replaced.
  3. default Wi-Fi regulatory country ES (ro.boot.wificountrycode) so channels 12/13 work before a SIM is present.
"""
import re
from pathlib import Path

DEV = Path.home() / 'kyf37-android10/device/kyocera/kyf37'
RADIO = DEV / 'radio'
RADIO.mkdir(exist_ok=True)

FILES = {
    # STA interface overlay: P2P must NOT be initialised on wlan0.
    'wpa_supplicant_overlay.conf': 'disable_scan_offload=1\np2p_disabled=1\ntdls_external_control=1\n',
    'p2p_supplicant_overlay.conf': 'disable_scan_offload=1\n',
}
for name, body in FILES.items():
    p = RADIO / name
    if not p.exists() or p.read_text() != body:
        p.write_text(body)
        print('wrote', p)
# keep the old top-level copy in step so nobody re-introduces the P2P bug through it
(DEV / 'wpa_supplicant_overlay.conf').write_text(FILES['wpa_supplicant_overlay.conf'])

MARK = '# radio-agent: vendor Wi-Fi config (p2p_disabled fix)'
mk = DEV / 'device.mk'
lines = mk.read_text().split('\n')

# 1. drop our own previous block (marker line, the continued PRODUCT_COPY_FILES statement, the country property)
out = []
i = 0
while i < len(lines):
    if lines[i] == MARK:
        i += 1
        while i < len(lines) and (lines[i].startswith('PRODUCT_COPY_FILES') or lines[i].startswith('    ') ):
            i += 1
        continue
    if lines[i].strip() == 'PRODUCT_PROPERTY_OVERRIDES += ro.boot.wificountrycode=ES':
        i += 1
        continue
    out.append(lines[i])
    i += 1
text = '\n'.join(out)

# 2. drop rules from other agents that install the same destinations
add = []
for name in FILES:
    dest = 'system/vendor/etc/wifi/' + name
    text, n = re.subn(r'[ \t]*\S+:' + re.escape(dest) + r'[ \t]*\\?[ \t]*(?=\n)', '', text)
    if n:
        print('removed %d earlier copy rule(s) for %s' % (n, dest))
    add.append('    device/kyocera/kyf37/radio/%s:%s' % (name, dest))

text = text.rstrip('\n') + '\n\n' + MARK + '\nPRODUCT_COPY_FILES += \\\n' + ' \\\n'.join(add) + '\n'
text += 'PRODUCT_PROPERTY_OVERRIDES += ro.boot.wificountrycode=ES\n'
mk.write_text(text)
print('device.mk updated')
