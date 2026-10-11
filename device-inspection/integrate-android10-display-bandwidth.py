from pathlib import Path
import subprocess
if subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Build active')
p=Path('/home/pablo/kyf37-android10/hardware/qcom-caf/msm8916/display/libhwcomposer/hwc_qclient.cpp')
s=p.read_text()
old='static bool updateDisplayBWCapForCam(bool on) {\n'
new=old+'#ifndef MDSS_MAX_BW_LIMIT_CAMERA\n    // This optional 8939-only interface is absent on the KYF37 MSM8909 kernel.\n    (void)on;\n    return false;\n#else\n'
if new not in s:
    assert old in s
    s=s.replace(old,new,1)
    end='    return true;\n}\n\nstatic void setCameraStatus'
    assert end in s
    s=s.replace(end,'    return true;\n#endif\n}\n\nstatic void setCameraStatus',1)
    p.write_text(s)
print('Unsupported optional 8939 camera bandwidth interface guarded; no synthetic kernel flag.')
