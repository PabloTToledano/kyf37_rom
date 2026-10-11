from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/base/core/java/android/content/pm/PackageParser.java';s=p.read_text();imports=[l for l in s.splitlines() if l.startswith('import') and 'NvAppProfileService' in l];assert len(imports)==1;name=imports[0][7:-1];print(name)
p=r/'external/robolectric-shadows/shadows/framework/src/main/java/org/robolectric/shadows/ShadowPackageParser.java';s=p.read_text();a='  private static class Callback implements PackageParser.Callback {\n'
if 'getAppProfileService()' not in s:s=s.replace(a,a+'\n    // Lineage platform callback extension; no NVIDIA service in the host test environment.\n    public '+name+' getAppProfileService() { return null; }\n');p.write_text(s)
