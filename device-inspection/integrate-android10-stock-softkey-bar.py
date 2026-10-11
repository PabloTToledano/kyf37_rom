"""Use original SystemUI artwork and the stock 116/88/116dp two-row footer."""
from pathlib import Path
import zipfile,hashlib,json,shutil

workspace=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree=Path('/home/pablo/kyf37-android10')
systemui=tree/'frameworks/base/packages/SystemUI'
names=['k_i_co_btn_softkey_base','k_c_co_btn_softkey_left_up_normal',
       'k_c_co_btn_softkey_left_down_normal','k_c_co_btn_softkey_center_normal',
       'k_c_co_btn_softkey_right_up_normal','k_c_co_btn_softkey_right_down_normal']
records=[]
with zipfile.ZipFile(workspace/'kyf37-rom/SystemUI-stock.apk') as archive:
    for name in names:
        entry='res/drawable-hdpi-v4/'+name+'.png'
        data=archive.read(entry)
        destination=systemui/'res/drawable-hdpi'/ (name+'.png')
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(data)
        records.append({'original_entry':entry,'sha256':hashlib.sha256(data).hexdigest()})
source=systemui/'src/com/android/systemui/statusbar/phone'
shutil.copyfile(workspace/'device-inspection/Kyf37SoftkeyBar.java',source/'Kyf37SoftkeyBar.java')
nav=source/'NavigationBarView.java'
text=nav.read_text()
anchor='''        mNavigationInflaterView.setButtonDispatchers(mButtonDispatchers);
'''
addition='''        if ("kyf37".equals(android.os.Build.DEVICE)) {
            mNavigationInflaterView.setVisibility(View.INVISIBLE);
            addView(new Kyf37SoftkeyBar(getContext()), new android.widget.FrameLayout.LayoutParams(
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT));
        }
'''
if 'new Kyf37SoftkeyBar' not in text:
    assert text.count(anchor)==1
    nav.write_text(text.replace(anchor,anchor+addition))
values=tree/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_softkey_dimensions.xml'
values.write_text('''<resources>
    <dimen name="navigation_bar_height">64dp</dimen>
    <dimen name="navigation_bar_height_landscape">64dp</dimen>
    <dimen name="navigation_bar_width">64dp</dimen>
</resources>
''')
policy=tree/'frameworks/base/services/core/java/com/android/server/policy/Kyf37Navigation.java'
text=policy.read_text()
method='''    private void publishPointerState() {
        context.sendBroadcastAsUser(new android.content.Intent("org.kyf37.POINTER_CHANGED")
                .putExtra("enabled", enabled), android.os.UserHandle.ALL,
                android.Manifest.permission.STATUS_BAR);
    }

'''
if 'private void publishPointerState()' not in text:
    text=text.replace('                enabled = false;','                enabled = false;\n                publishPointerState();')
    text=text.replace('        Toast.makeText(context, enabled','        publishPointerState();\n        Toast.makeText(context, enabled')
    text=text.replace('    private void touch(int action) {',method+'    private void touch(int action) {')
    policy.write_text(text)
(workspace/'kyf37-rom/android10-stock-softkey-artwork.json').write_text(json.dumps({
    'source':'Owner stock SystemUI APK','assets':records,'stock_layout_reference':
    'device-inspection/stock-navigation-bar-layout.txt',
    'geometry_dp':{'left_width':116,'center_width':88,'right_width':116,'row_height':32},
    'labels':'Current global physical-key actions; OEM per-app dynamic label ABI is not yet restored',
    'hardware_verified':False},indent=2)+'\n')
print('Original softkey artwork and geometry integrated into Android 10 SystemUI')
