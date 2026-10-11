from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/base/packages/SettingsLib/src/com/android/settingslib/deviceinfo/AbstractWifiMacAddressPreferenceController.java'
s=p.read_text().replace('''public boolean isAvailable() {
        return true;
    }''','''public boolean isAvailable() {
        return mWifiManager != null;
    }''')
s=s.replace('''        final String[] macAddresses = mWifiManager.getFactoryMacAddresses();''','''        // Some devices have no Wi-Fi hardware/service. Never query an absent manager.
        if (mWifiMacAddress == null) return;
        if (mWifiManager == null) {
            mWifiMacAddress.setSummary(R.string.status_unavailable);
            return;
        }
        final String[] macAddresses = mWifiManager.getFactoryMacAddresses();''')
p.write_text(s)
for p in r.glob('frameworks/base/packages/SettingsLib/tests/**/AbstractWifiMacAddressPreferenceControllerTest.java'):
 print(p);print(p.read_text())
p=r/'frameworks/base/libs/hwui/Properties.h'
for i,l in enumerate(p.read_text().splitlines()):
 if 'PARTIAL' in l or 'BUFFER_AGE' in l:print(i+1,l)
