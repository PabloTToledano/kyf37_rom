"""Final v22 product policy: native flashlight supersedes legacy MobileLight."""
from pathlib import Path
import re, shutil
tree = Path('/home/pablo/kyf37-android10')
mk = tree/'packages/apps/Kyf37Flashlight/Android.mk'
text = mk.read_text()
if 'LOCAL_OVERRIDES_PACKAGES := MobileLight' not in text:
    text = text.replace('include $(BUILD_PACKAGE)', 'LOCAL_OVERRIDES_PACKAGES := MobileLight\ninclude $(BUILD_PACKAGE)')
    mk.write_text(text)
# Keep the legacy APK as a porting input, but omit its prebuilt product module.
mk = tree/'packages/apps/Kyf37StockApps/Android.mk'
text = mk.read_text()
new, count = re.subn(r'include \$\(CLEAR_VARS\)\nLOCAL_MODULE := MobileLight\n.*?include \$\(BUILD_PREBUILT\)\n', '', text, flags=re.S)
assert count <= 1
if new != text: mk.write_text(new)
# Android does not remove obsolete installed outputs automatically.
target = tree/'out/target/product/kyf37/system/app/MobileLight'
assert target.resolve().is_relative_to(tree/'out/target/product/kyf37/system/app')
if target.exists(): shutil.rmtree(target)
print('Native flashlight overrides MobileLight; legacy prebuilt/output excluded')
