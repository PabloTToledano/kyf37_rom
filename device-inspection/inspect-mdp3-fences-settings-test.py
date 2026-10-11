from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss')
for p in r.glob('mdp3*.c'):
 lines=p.read_text().splitlines()
 for i,l in enumerate(lines):
  if 'RETIRE_FENCE' in l or 'MSMFB_BUFFER_SYNC' in l or 'MDP_BUF_SYNC_FLAG' in l:print(p.name,i+1,'\n'.join(lines[max(0,i-4):i+8]))
p=Path('/home/pablo/kyf37-android10/frameworks/base/packages/SettingsLib/tests/robotests/src/com/android/settingslib/deviceinfo/WifiMacAddressPreferenceControllerTest.java')
s=p.read_text();anchor='    private static class ConcreteWifiMacAddressPreferenceController'
add='''    @Test
    public void missingWifiManager_preferenceUnavailableAndNoCrash() {
        doReturn(null).when(mContext).getSystemService(WifiManager.class);
        mController = new ConcreteWifiMacAddressPreferenceController(mContext, mLifecycle);
        assertThat(mController.isAvailable()).isFalse();
        mController.displayPreference(mScreen);
    }

    @Test
    public void missingPreference_updateDoesNotCrash() {
        doReturn(null).when(mScreen)
                .findPreference(AbstractWifiMacAddressPreferenceController.KEY_WIFI_MAC_ADDRESS);
        mController.displayPreference(mScreen);
    }

'''
if 'missingWifiManager_preferenceUnavailableAndNoCrash' not in s:s=s.replace(anchor,add+anchor);p.write_text(s)
