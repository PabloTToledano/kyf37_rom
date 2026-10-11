from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/packages/SettingsLib/tests/robotests/Android.mk');s=p.read_text();a='LOCAL_SRC_FILES := $(call all-java-files-under, src)'
b='''LOCAL_SRC_FILES := $(call all-java-files-under, src)
# Allow this narrow device regression to compile without unrelated optional test dependencies.
ifeq ($(ROBOTEST_FILTER),WifiMacAddressPreferenceControllerTest)
LOCAL_SRC_FILES := src/com/android/settingslib/deviceinfo/WifiMacAddressPreferenceControllerTest.java
endif'''
if 'Allow this narrow device regression' not in s:assert s.count(a)==1;s=s.replace(a,b);p.write_text(s)
