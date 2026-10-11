from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/base/core/java/android/content/pm/PackageParser.java';s=p.read_text();a=s.find('interface Callback');print(s[a:a+2300])
p=r/'external/robolectric-shadows/shadows/framework/src/main/java/org/robolectric/shadows/ShadowPackageParser.java';print(p.read_text()[2000:4700])
