from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java')
s=p.read_text()
a='''                            if ((mEndcallBehavior
                                    & Settings.System.END_BUTTON_BEHAVIOR_HOME) != 0) {'''
b='''                            // KYF37: outside a call the hang-up key is always Home.
                            if (mKyf37Navigation != null || (mEndcallBehavior
                                    & Settings.System.END_BUTTON_BEHAVIOR_HOME) != 0) {'''
if 'outside a call the hang-up key is always Home' not in s:
    assert s.count(a)==1
    p.write_text(s.replace(a,b))
print('ok')
