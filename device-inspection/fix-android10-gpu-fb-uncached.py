"""gpu agent: allocate the SurfaceFlinger client-target (GRALLOC_USAGE_HW_FB) ION buffers UNCACHED (like the stock fb0 memory).
Switch: persist.kyf37.fb_uncached (default 1; set 0 for the old cached behaviour; read at every allocation, so
`setprop` + `ctl.restart surfaceflinger` is enough). WSL, idempotent."""
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/hardware/qcom-caf/msm8916/display/libgralloc/alloc_controller.cpp')
s = p.read_text()
if 'kyf37FbUncached' in s:
    print('already patched'); raise SystemExit
s = s.replace('#include <string.h>\n', '#include <string.h>\n#include <cutils/properties.h>\n', 1)
old = 'static bool useUncached(const int& usage) {\n'
new = '''static bool kyf37FbUncached() {
    char v[PROPERTY_VALUE_MAX];
    property_get("persist.kyf37.fb_uncached", v, "1");
    return v[0] != '0';
}

static bool useUncached(const int& usage) {
    // KYF37: scanout (client target) buffers are written by the GPU and read by MDP3 only; keep them out of the CPU cache.
    if ((usage & GRALLOC_USAGE_HW_FB) && kyf37FbUncached())
        return true;
'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)
print('patched')
