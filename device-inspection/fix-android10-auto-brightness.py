#!/usr/bin/env python3
"""Idempotent: turn on Android automatic brightness for the KYF37 using the LV5216 photosensor exposed as android.sensor.light
(device-inspection/sensors/sensors.cpp, sensors.kyf37_extra; node /sys/class/leds/backlightinfo/ambient_light_level, 16 levels).
Framework defaults are config_automatic_brightness_available=false and EMPTY brightness arrays ('must be overridden in platform
overlays'); Lineage does not set them, so the device overlay (DEVICE_PACKAGE_OVERLAYS) defines them.
Lux scale = luxForLevel[] in sensors.cpp (0,2,6,15,35,70,120,200,320,500,800,1200,2000,3500,6000,10000: approximate, uncalibrated).
Curve: 7 lux break points (n) -> 8 backlight values (n+1), 0..255, non-decreasing; min user setting is 10 (framework default).
Run in WSL; takes effect with the next framework-res build (needs a ROM flash, or a runtime overlay for live tests)."""
import pathlib
T = pathlib.Path.home() / 'kyf37-android10'
d = T / 'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values'
d.mkdir(parents=True, exist_ok=True)
LEVELS = [2, 15, 70, 200, 500, 1200, 3500]
VALUES = [20, 35, 55, 85, 120, 170, 215, 255]
assert len(VALUES) == len(LEVELS) + 1 and VALUES == sorted(VALUES) and all(0 <= v <= 255 for v in VALUES)
xml = '''<?xml version="1.0" encoding="utf-8"?>
<!-- KYF37 automatic brightness (fix-android10-auto-brightness.py). Lux values come from the LV5216 photosensor HAL. -->
<resources>
    <bool name="config_automatic_brightness_available">true</bool>
    <integer-array name="config_autoBrightnessLevels">
%s
    </integer-array>
    <integer-array name="config_autoBrightnessLcdBacklightValues">
%s
    </integer-array>
    <integer name="config_autoBrightnessBrighteningLightDebounce">2000</integer>
    <integer name="config_autoBrightnessDarkeningLightDebounce">4000</integer>
</resources>
''' % ('\n'.join('        <item>%d</item>' % v for v in LEVELS), '\n'.join('        <item>%d</item>' % v for v in VALUES))
f = d / 'kyf37_auto_brightness.xml'
if not f.exists() or f.read_text() != xml:
    f.write_text(xml, newline=chr(10)); print('wrote', f)
else:
    print('overlay up to date')
print('done')
