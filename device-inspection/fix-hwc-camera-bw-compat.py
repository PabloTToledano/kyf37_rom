from pathlib import Path
p=Path('/home/pablo/kyf37-lineage/hardware/qcom/display-caf/msm8916/libhwcomposer/hwc_qclient.cpp')
s=p.read_text()
start='static bool updateDisplayBWCapForCam(bool on) {\n'
end='    return true;\n}\n\nstatic void setCameraStatus'
patched=start+'''#ifndef MDSS_MAX_BW_LIMIT_CAMERA
    // This kernel has no camera bandwidth-cap API; callers handle false.
    (void)on;
    return false;
#else
'''
if patched not in s:
 assert s.count(start)==1 and s.count(end)==1
 s=s.replace(start,patched,1).replace(end,'    return true;\n#endif\n}\n\nstatic void setCameraStatus',1)
 p.write_text(s)
print('Unsupported kernel camera bandwidth-cap path guarded')
