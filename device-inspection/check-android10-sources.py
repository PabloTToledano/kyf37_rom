"""Fetch pinned Android 10 reference files for offline KYF37 bring-up review."""
import base64, hashlib, json, urllib.request
from pathlib import Path

root = Path('kyf37-rom/android10-reference')
root.mkdir(parents=True, exist_ok=True)
files = {
    'go_defaults.mk': ('build', 'target/product/go_defaults.mk'),
    'libbinder-Android.bp': ('frameworks/native', 'libs/binder/Android.bp'),
    'libhwbinder-Android.bp': ('system/libhwbinder', 'Android.bp'),
    'lmkd.c': ('system/core', 'lmkd/lmkd.c'),
    'go_defaults_common.mk': ('build', 'target/product/go_defaults_common.mk'),
    'go_defaults.prop': ('build', 'target/board/go_defaults.prop'),
    'go_defaults_common.prop': ('build', 'target/board/go_defaults_common.prop'),
    'seccomp_policy.cpp': ('bionic', 'libc/seccomp/seccomp_policy.cpp'),
    'Window.java': ('frameworks/base', 'core/java/android/view/Window.java'),
    'Canvas.java': ('frameworks/base', 'graphics/java/android/graphics/Canvas.java'),
    'FloatMath.java': ('frameworks/base', 'core/java/android/util/FloatMath.java'),
    'Pools.java': ('frameworks/base', 'core/java/android/util/Pools.java'),
    'SystemProperties.java': ('frameworks/base', 'core/java/android/os/SystemProperties.java'),
    'ContactsContract.java': ('frameworks/base', 'core/java/android/provider/ContactsContract.java'),
}
report = {'tag': 'android-10.0.0_r47', 'files': {}, 'errors': {}}
for name, (repo, path) in files.items():
    url = f'https://android.googlesource.com/platform/{repo}/+/android-10.0.0_r47/{path}?format=TEXT'
    try:
        content = base64.b64decode(urllib.request.urlopen(url, timeout=45).read())
        (root / name).write_bytes(content)
        report['files'][name] = {'url': url, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
    except Exception as exc:
        report['errors'][name] = str(exc)
(root / 'provenance.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
