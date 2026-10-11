from pathlib import Path
import subprocess
if subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Build active')
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/inputmethod/InputMethodUtils.java')
s=p.read_text()
marker='        // We\'d prefer to fall back on a system IME, since that is safer.\n'
patch='''        // A physical-key-only KYF37 needs its multi-tap IME for automatic fallback.
        // This routine is not used to override an explicitly selected working IME.
        if (android.os.SystemProperties.getBoolean("ro.kyf37.keypad_navigation", false)) {
            for (InputMethodInfo imi : enabledImes) {
                if (imi.isSystem() && !imi.isAuxiliaryIme()
                        && "org.kyf37.keypadime".equals(imi.getPackageName())) {
                    return imi;
                }
            }
        }
'''
if patch not in s:
    assert marker in s
    p.write_text(s.replace(marker,patch+marker,1))
print('KYF37 automatic enabled-IME fallback prefers physical multi-tap keyboard.')
