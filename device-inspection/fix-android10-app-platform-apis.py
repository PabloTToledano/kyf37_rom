from pathlib import Path
tree=Path('/home/pablo/kyf37-android10')
for rel in ['packages/apps/Kyf37Home/Android.mk','packages/apps/Kyf37OuterScreen/Android.mk','packages/inputmethods/Kyf37KeypadIME/Android.mk']:
 p=tree/rel;s=p.read_text()
 if 'LOCAL_SDK_VERSION' in s:
  s=s.replace('LOCAL_PRIVATE_PLATFORM_APIS := true\n','')
 elif 'LOCAL_PRIVATE_PLATFORM_APIS' not in s:s=s.replace('include $(BUILD_PACKAGE)','LOCAL_PRIVATE_PLATFORM_APIS := true\ninclude $(BUILD_PACKAGE)',1)
 p.write_text(s)
print('Declared platform API use for platform-signed KYF37 apps')
