"""Add the original Kyocera ringtones/notifications/alarms (and set them as defaults). WSL; idempotent."""
from pathlib import Path
import shutil
stock = Path('/home/pablo/kyf37-rom/stock-system/media/audio')
dev = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
lines = []
for kind in ('ringtones', 'notifications', 'alarms'):
    dst = dev/'audio'/kind; dst.mkdir(parents=True, exist_ok=True)
    for f in sorted((stock/kind).glob('*.mp3')):
        shutil.copy2(f, dst/f.name)
        lines.append(f'device/kyocera/kyf37/audio/{kind}/{f.name}:system/media/audio/{kind}/{f.name}')
BS = chr(92); NL = chr(10)
mk = dev/'audio-oem-sounds.mk'
mk.write_text('PRODUCT_COPY_FILES += ' + BS + NL + '    ' + (' ' + BS + NL + '    ').join(lines) + NL + NL +
              'PRODUCT_PROPERTY_OVERRIDES += ro.config.ringtone=02_rt.mp3 ro.config.notification_sound=03_nt.mp3 ro.config.alarm_alert=01_al_alarm01.mp3' + NL)
p = dev/'device.mk'; s = p.read_text()
inc = '$(call inherit-product, device/kyocera/kyf37/audio-oem-sounds.mk)'
if inc not in s: p.write_text(s.rstrip() + '\n' + inc + '\n')
print(len(lines), 'sound files wired')
