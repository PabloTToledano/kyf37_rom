from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'packages/apps/Bluetooth/src/com/android/bluetooth/btservice/AdapterState.java'
s=p.read_text().replace('static final int BLE_START_TIMEOUT_DELAY = 4000;', 'static final int BLE_START_TIMEOUT_DELAY = android.os.Build.DEVICE.equals("kyf37") ? 15000 : 4000;')
p.write_text(s)
p=root/'device/kyocera/kyf37/device.mk'
s=p.read_text()
line='PRODUCT_PROPERTY_OVERRIDES += bluetooth.enable_timeout_ms=15000'
if line not in s:p.write_text(s.rstrip()+'\n'+line+'\n')
p=root/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
a='''        // An open KYF37 must wake from its physical keypad.'''
b='''        // The exterior side key lights the outer clock while the lid remains closed.
        if (mKyf37Navigation != null && !isInjected
                && keyCode == KeyEvent.KEYCODE_CAMERA
                && mDefaultDisplayPolicy.getLidState() == LID_CLOSED) {
            if (down && event.getRepeatCount() == 0) {
                mHandler.post(new Runnable() { public void run() {
                    Intent service = new Intent("org.kyf37.action.OUTER_WAKE");
                    service.setComponent(new ComponentName("org.kyf37.subdisplay",
                            "org.kyf37.subdisplay.OuterScreenService"));
                    mContext.startServiceAsUser(service, UserHandle.SYSTEM);
                }});
            }
            return 0;
        }

'''
if 'The exterior side key lights the outer clock' not in s:
 assert s.count(a)==1
 s=s.replace(a,b+a)
 p.write_text(s)
for name in ('qpnp_pon.kl','gpio-keys.kl'):
 p=root/'device/kyocera/kyf37/keylayout'/name
 s=p.read_text()
 import re
 s=re.sub(r'^(key\s+\d+\s+(?:CAMERA|ENDCALL))\s*$',r'\1 WAKE',s,flags=re.M)
 p.write_text(s)
p=root/'packages/apps/Kyf37OuterScreen/src/org/kyf37/subdisplay/OuterScreenService.java'
s=p.read_text()
s=s.replace('private int battery=0;', '''private int battery=0;
    private final Handler handler=new Handler();
    private long visibleUntil;
    private boolean wasClosed;
    private final Runnable blank=new Runnable() {
        @Override public void run() {refresh();}
    };''')
s=s.replace('boolean visible=!SystemProperties.getBoolean("sys.kyf37.lid_open",true);', '''boolean closed=!SystemProperties.getBoolean("sys.kyf37.lid_open",true);
        long elapsed=SystemClock.elapsedRealtime();
        if(closed && !wasClosed) visibleUntil=elapsed+10000;
        if(!closed) visibleUntil=0;
        wasClosed=closed;
        boolean visible=closed && elapsed<visibleUntil;
        handler.removeCallbacks(blank);
        if(visible) handler.postDelayed(blank,visibleUntil-elapsed);''')
s=s.replace('@Override public int onStartCommand(Intent intent,int flags,int id) {refresh();return START_STICKY;}', '''@Override public int onStartCommand(Intent intent,int flags,int id) {
        if(intent!=null && "org.kyf37.action.OUTER_WAKE".equals(intent.getAction())
                && !SystemProperties.getBoolean("sys.kyf37.lid_open",true)) {
            visibleUntil=SystemClock.elapsedRealtime()+10000;
        }
        refresh();return START_STICKY;
    }''')
s=s.replace('unregisterReceiver(changes);unregisterReceiver(lid);alarms.cancel(tick);', 'handler.removeCallbacks(blank);unregisterReceiver(changes);unregisterReceiver(lid);alarms.cancel(tick);')
p.write_text(s)
print('Closed-lid CAMERA side key: outer clock for 10 seconds; main screen stays asleep')
print('KYF37 Bluetooth startup deadlines allow original 5-second transport power-on')
