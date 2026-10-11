#!/usr/bin/env python3
"""microG's manifest declares meta-data fake-signature as @string/..., PackageParser stores that as an int, so
getString() is null and neither Lineage's generateFakeSignature nor mayFakeSignature spoofed anything (Self-Check
'System spoofs signature' unticked). Resolve the reference from the APK's resources. Idempotent."""
import pathlib
f = pathlib.Path.home() / 'kyf37-android10/frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java'
t = f.read_text()
if 'fakeSignatureString(' in t:
    print('already patched'); raise SystemExit
helper = '''    private static String fakeSignatureString(PackageParser.Package p) {
        Bundle md = p.mAppMetaData;
        if (md == null) return null;
        String s = md.getString("fake-signature");
        if (s != null) return s;
        int id = md.getInt("fake-signature", 0);
        if (id == 0) return null;
        try {
            android.content.res.AssetManager am = new android.content.res.AssetManager();
            am.addAssetPath(p.baseCodePath);
            Resources r = new Resources(am, null, null);
            return r.getString(id);
        } catch (Throwable e) {
            Log.w(TAG, "fake-signature resource not resolvable", e);
            return null;
        }
    }

'''
a = '    private static Optional<Signature> generateFakeSignature('
assert t.count(a) == 1
t = t.replace(a, helper + a)
old = '''        Bundle metadata = p.mAppMetaData;
        if (metadata == null) {
            return Optional.empty();
        }

        String fakeSignatureStr = metadata.getString("fake-signature");
'''
assert t.count(old) == 1
t = t.replace(old, '        String fakeSignatureStr = fakeSignatureString(p);\n')
old2 = '''                    && p.mAppMetaData != null) {
                String sig = p.mAppMetaData.getString("fake-signature");'''
assert t.count(old2) == 1
t = t.replace(old2, '''                    && p.mAppMetaData != null) {
                String sig = fakeSignatureString(p);''')
f.write_text(t); print('patched')
