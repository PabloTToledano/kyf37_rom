"""Stub the Kyocera extensions of android.hardware.Camera that the original Kyocera Camera app links against,
and make the camera provider start after the camera daemon. WSL; idempotent.

Stock framework additions found by diffing base-framework-smali against Android 10:
4 callback interfaces + 11 public methods (their natives were Kyocera libandroid_runtime code).
"""
from pathlib import Path
root = Path('/home/pablo/kyf37-android10')
cam = root / 'frameworks/base/core/java/android/hardware/Camera.java'
s = cam.read_text()
MARK = 'KYF37 Kyocera Camera API stubs'
if MARK not in s:
    stubs = '''
    // ---- KYF37 Kyocera Camera API stubs: the original Kyocera Camera app links against these. ----
    /** @hide */ public interface AutoSceneCallback { void onAutoSceneDetection(byte scene, Camera camera); }
    /** @hide */ public interface ContinuousShootingTakePicCallback { void onContinuousShootingTakePicCallback(); }
    /** @hide */ public interface SmileShutterCallback { void onRequestShutter(); }
    /** @hide */ public interface TakePicAvailDelayCallback { void onTakePictureAvailableDelay(int delay, Camera camera); }
    private AutoSceneCallback mKcAutoSceneCallback;
    private ContinuousShootingTakePicCallback mKcContinuousCallback;
    private SmileShutterCallback mKcSmileCallback;
    private TakePicAvailDelayCallback mKcDelayCallback;
    /** @hide */ public final void setAutoSceneCallback(AutoSceneCallback cb) { mKcAutoSceneCallback = cb; }
    /** @hide */ public final void setContinuousShootingTakePicCallback(ContinuousShootingTakePicCallback cb) { mKcContinuousCallback = cb; }
    /** @hide */ public final void setSmileShutterCallback(SmileShutterCallback cb) { mKcSmileCallback = cb; }
    /** @hide */ public final void setTakePicAvailableDelayCallback(TakePicAvailDelayCallback cb) { mKcDelayCallback = cb; }
    /** @hide */ public final void prepareGetLowLightIntensity() { }
    /** @hide */ public final void sendGyroscopeData(int a, int b, int c, int d) { }
    /** @hide */ public final void startContinuousShooting(int count, PictureCallback jpeg) { }
    /** @hide */ public final void stopContinuousShooting() { }
    /** @hide */ public final void startHarrisShutter(PictureCallback jpeg) { }
    /** @hide */ public final void stopHarrisShutter() { }
    /** @hide */ public final void stopLongshot() { }
'''
    needle = 'public class Camera {'
    assert s.count(needle) == 1, 'unexpected Camera.java layout'
    s = s.replace(needle, needle + stubs, 1)
    cam.write_text(s)

d = root / 'device/kyocera/kyf37'
(d / 'init.kyf37.camera.rc').write_text('''# The camera provider enumerates sensors once at start. The OEM daemon must already be running,
# otherwise Android reports zero cameras for the whole boot.
service kyf37-camera-order /system/bin/sh -c "sleep 4; setprop ctl.restart vendor.camera-provider-2-4"
    user root
    oneshot
    disabled

on property:init.svc.qcamerasvr=running
    start kyf37-camera-order
''')
p = d / 'device.mk'; t = p.read_text()
line = 'PRODUCT_COPY_FILES += device/kyocera/kyf37/init.kyf37.camera.rc:system/etc/init/init.kyf37.camera.rc'
if line not in t: p.write_text(t.rstrip() + '\n' + line + '\n')
print('camera kc api stubs + ordering rc installed')
