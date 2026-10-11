#!/usr/bin/env python3
"""Idempotent: outer screen v2 = Java-rendered clock (proper font, date, unread badge), incoming/in-call/missed-call screen and
notification screen with marquee, on top of the native mascot/scene layer. Must run AFTER fix-android10-outer-animation.py,
-outer-badapple.py and -outer-settings.py (they regenerate OuterScreenService.java); each run re-applies the patch.
Files: device-inspection/outer-v2/{OuterUi.java,NotifListener.java,service-members.java.inc}. Run in WSL."""
import pathlib, re
WS = pathlib.Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection')
app = pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37OuterScreen'
src = app / 'src/org/kyf37/subdisplay'
for n in ('OuterUi.java', 'NotifListener.java', 'PixFont.java'):
    (src / n).write_text((WS / 'outer-v2' / n).read_text(), newline='\n')

(app / 'assets').mkdir(exist_ok=True)
(app / 'assets/outerfont.bin').write_bytes((WS / 'outer-v2/outerfont.bin').read_bytes())
svc = src / 'OuterScreenService.java'
s = svc.read_text()
MARK = 'KYF37_OUTER_V2'
if MARK not in s:
    def rep(old, new, count=1):
        global s
        assert old in s, 'anchor missing: ' + old[:60]
        s = s.replace(old, new, count)
    rep('    private static native int updateVideo(byte[] packed);',
        '    private static native int updateVideo(byte[] packed);\n    private static native byte[] renderLayer(int frame,int scene,int phase);')
    rep('int result=updateAnimation(frame++,now.get(Calendar.HOUR_OF_DAY),\n                now.get(Calendar.MINUTE),battery,scene);',
        'int result=drawFrame(frame++,now,scene);')
    rep('result=updateAnimation(-1,now.get(Calendar.HOUR_OF_DAY),now.get(Calendar.MINUTE),battery,\n                    (int)((SystemClock.elapsedRealtime()/5000)&3));',
        'result=drawFrame(-1,now,(int)((SystemClock.elapsedRealtime()/5000)&3));')
    rep('private boolean lit(){return movie||animating||', 'private boolean lit(){return movie||animating||alert!=null||')
    rep('        if(animating || movie)return;\n        PowerManager.WakeLock lock',
        '        if(lidClosed && alert==null && callState!=android.telephony.TelephonyManager.CALL_STATE_IDLE)showCallAlert();\n'
        '        if(animating || movie || alert!=null)return;\n        PowerManager.WakeLock lock')
    rep('        if(!lidClosed) {sideHeld=false;', '        if(!lidClosed) {clearAlert();sideHeld=false;')
    rep('        if(down) {\n            if(movie)', '        if(down) {\n            if(alert!=null){if(alert.kind!=OuterUi.K_RING){clearAlert();light();refresh();}return;}\n            if(movie)')
    rep('        if(intent!=null && "org.kyf37.action.OUTER_WAKE".equals(intent.getAction()) && closed()) {',
        '        if(intent!=null && "org.kyf37.action.OUTER_WAKE".equals(intent.getAction()) && closed()) {\n            if(alert!=null)return START_STICKY;')
    rep('    @Override public int onStartCommand(Intent intent,int flags,int id) {\n',
        '    @Override public int onStartCommand(Intent intent,int flags,int id) {\n        if(intent!=null && "org.kyf37.action.OUTER_DEBUG_ALERT".equals(intent.getAction())){debugAlert(intent);return START_STICKY;}\n')
    rep('        super.onCreate();\n','        super.onCreate();\n        instance=this;\n        PixFont.load(getAssets());\n        enableNotificationListener();\n'
        '        ((android.telephony.TelephonyManager)getSystemService(TELEPHONY_SERVICE)).listen(phoneListener,android.telephony.PhoneStateListener.LISTEN_CALL_STATE);\n')
    rep('    @Override public IBinder onBind(Intent intent) {return null;}',
        (WS / 'outer-v2/service-members.java.inc').read_text() + '    @Override public IBinder onBind(Intent intent) {return null;}')
    rep('        inputRunning=false;sideHeld=false;handler.removeCallbacks(longSide);stopMovie();\n        stopAnimation();',
        '        instance=null;clearAlert();\n        ((android.telephony.TelephonyManager)getSystemService(TELEPHONY_SERVICE)).listen(phoneListener,android.telephony.PhoneStateListener.LISTEN_NONE);\n'
        '        inputRunning=false;sideHeld=false;handler.removeCallbacks(longSide);stopMovie();\n        stopAnimation();')
    svc.write_text(s, newline='\n'); print('service patched')
else:
    print('service already patched')

mf = app / 'AndroidManifest.xml'
m = mf.read_text()
if 'NotifListener' not in m:
    perms = ''.join('    <uses-permission android:name="android.permission.%s"/>\n' % p for p in
                    ('READ_PHONE_STATE', 'READ_CONTACTS', 'READ_CALL_LOG', 'MANAGE_NOTIFICATION_LISTENERS'))
    m = m.replace('    <application', perms + '    <application', 1)
    m = m.replace('        <service android:name=".OuterScreenService" android:exported="false"/>',
        '        <service android:name=".OuterScreenService" android:exported="false"/>\n'
        '        <service android:name=".NotifListener" android:exported="false" android:label="KYF37 outer screen"\n'
        '            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">\n'
        '            <intent-filter><action android:name="android.service.notification.NotificationListenerService"/></intent-filter>\n'
        '        </service>', 1)
    mf.write_text(m, newline='\n'); print('manifest patched')

m2 = mf.read_text()
if 'READ_PRIVILEGED_PHONE_STATE' in m2:  # signature|privileged without a privapp allowlist crashes system_server
    mf.write_text(''.join(l for l in m2.splitlines(True) if 'READ_PRIVILEGED_PHONE_STATE' not in l), newline=chr(10)); print('removed privileged permission')

# native: clock-less layer for the Java compositor
r = app / 'render.c'
t = r.read_text()
if 'g_noclock' not in t:
    t = t.replace('static int g_size=2,', 'static int g_noclock=0;\nvoid kyf37_subdisplay_noclock(int on){g_noclock=on;}\nstatic int g_size=2,', 1)
    t = t.replace(' int s=g_size+1,h=hour,pm=0;', ' if(g_noclock)return;\n int s=g_size+1,h=hour,pm=0;', 1)
    assert 'if(g_noclock)return;' in t
    r.write_text(t, newline='\n'); print('render.c patched')
h = app / 'render.h'
ht = h.read_text()
if 'kyf37_subdisplay_noclock' not in ht:
    h.write_text(ht + '\nvoid kyf37_subdisplay_noclock(int on);\n', newline='\n')
c = app / 'controller.c'
ct = c.read_text()
if 'renderLayer' not in ct:
    ct += '''
/* KYF37_OUTER_V2: mascot/actor layer without the native clock; the Java side draws the clock and sends the frame. */
JNIEXPORT jbyteArray JNICALL Java_org_kyf37_subdisplay_OuterScreenService_renderLayer(JNIEnv *env,jclass type,jint frame,jint scene,jint phase) {
    (void)type;
    unsigned char pixels[128*36];
    kyf37_subdisplay_noclock(1);
    int result=frame<0?kyf37_subdisplay_idle(pixels,sizeof pixels,0,0,0,phase):kyf37_subdisplay_animation(pixels,sizeof pixels,frame,0,0,0,scene);
    kyf37_subdisplay_noclock(0);
    if(result)return NULL;
    jbyteArray out=(*env)->NewByteArray(env,128*36);
    if(!out)return NULL;
    (*env)->SetByteArrayRegion(env,out,0,128*36,(const jbyte*)pixels);
    return out;
}
'''
    c.write_text(ct, newline='\n'); print('controller.c patched')
print('done')

# NotificationManager refuses listeners on low-RAM (Go) devices unless the package is allow-listed: static overlay package.
ov = pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37OuterOverlay'
(ov / 'res/values').mkdir(parents=True, exist_ok=True)
files = {
    'Android.mk': 'LOCAL_PATH := $(call my-dir)\ninclude $(CLEAR_VARS)\nLOCAL_PACKAGE_NAME := Kyf37OuterOverlay\nLOCAL_MODULE_TAGS := optional\n'
                  'LOCAL_CERTIFICATE := platform\nLOCAL_IS_RUNTIME_RESOURCE_OVERLAY := true\nLOCAL_MODULE_PATH := $(TARGET_OUT_VENDOR)/overlay\n'
                  'LOCAL_SDK_VERSION := current\ninclude $(BUILD_PACKAGE)\n',
    'AndroidManifest.xml': '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.overlay.outer">\n'
                           '    <overlay android:targetPackage="android" android:isStatic="true" android:priority="40"/>\n'
                           '    <application android:hasCode="false"/>\n</manifest>\n',
    'res/values/config.xml': '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                             '    <string-array name="config_allowedManagedServicesOnLowRamDevices" translatable="false">\n'
                             '        <item>org.kyf37.subdisplay</item>\n    </string-array>\n</resources>\n',
}
for name, text in files.items():
    f = ov / name
    if not f.exists() or f.read_text() != text:
        f.write_text(text, newline=chr(10)); print('wrote', f)
mk = pathlib.Path.home() / 'kyf37-android10/device/kyocera/kyf37/device.mk'
dm = mk.read_text()
if 'Kyf37OuterOverlay' not in dm:
    mk.write_text(dm.rstrip(chr(10)) + chr(10) + 'PRODUCT_PACKAGES += Kyf37OuterOverlay' + chr(10), newline=chr(10)); print('device.mk: Kyf37OuterOverlay')
