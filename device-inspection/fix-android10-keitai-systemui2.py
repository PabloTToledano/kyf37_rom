"""Keitai standby/notification polish, pass 2. Run in WSL after fix-android10-keitai-systemui.py.

- Notification rows: flat, square-cornered, 2 dp navy frame (no rounded Material cards).
- D-pad selection: square translucent-blue fill with a navy frame instead of a rounded outline.
- Standby date: Japanese keitai order "10/8 (Thu)" instead of "Thu, Oct 8".
- Standby clock plate: square, double-weight frame.
- Soft-key bar: locked => "Menu | OK Unlock | Camera-less" labels; unlocked unchanged.
"""
from pathlib import Path

root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
here = Path(__file__).resolve().parent

def patch(path, old, new, marker):
    s = path.read_text()
    if marker in s:
        return
    assert old in s, (path, old)
    path.write_text(s.replace(old, new, 1))

# 1. Square notification rows (outline + background radius = 0 on kyf37).
patch(root / 'src/com/android/systemui/statusbar/notification/row/ExpandableOutlineView.java',
      '        setClipToOutline(mAlwaysRoundBothCorners);\n    }',
      '        if (android.os.Build.DEVICE.equals("kyf37")) mOutlineRadius = 0; // Keitai flat rows\n'
      '        setClipToOutline(mAlwaysRoundBothCorners);\n    }',
      'Keitai flat rows')

p = root / 'res/drawable/notification_material_bg.xml'
s = p.read_text()
s = s.replace('<stroke android:width="1dp" android:color="#667C91" />',
              '<stroke android:width="2dp" android:color="#2C5A86" />')
if 'android:radius="0dp"' not in s:
    s = s.replace('</shape>', '    <corners android:radius="0dp" />\n        </shape>')
p.write_text(s)

# 2. Square selection highlight.
p = here / 'Kyf37KeitaiKeys.java.txt'
s = p.read_text()
s = s.replace('border.setColor(Color.TRANSPARENT);', 'border.setColor(0x402475BB);')
s = s.replace('border.setCornerRadius(3 * window.getResources().getDisplayMetrics().density);',
              'border.setCornerRadius(0);')
s = s.replace('0xff2475bb', '0xff10305a')
p.write_text(s)
(root / 'src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java').write_text(s)

# 3. Keitai date order.
patch(root / 'src/com/android/systemui/keyguard/KeyguardSliceProvider.java',
      '            DateFormat format = DateFormat.getInstanceForSkeleton(mDatePattern, l);',
      '            DateFormat format = android.os.Build.DEVICE.equals("kyf37")\n'
      '                    ? new android.icu.text.SimpleDateFormat("M/d (EEE)", l) // Keitai date\n'
      '                    : DateFormat.getInstanceForSkeleton(mDatePattern, l);',
      'Keitai date')

# 4. Square clock plate with heavier frame.
(root / 'res/drawable/keitai_standby_plate.xml').write_text('''<shape xmlns:android="http://schemas.android.com/apk/res/android">
 <solid android:color="#CC142638"/><stroke android:width="2dp" android:color="#B4D7EF"/>
 <corners android:radius="0dp"/>
</shape>
''')

# 5. Soft-key legend while locked: OK unlocks, F1 is not a menu there.
patch(root / 'src/com/android/systemui/statusbar/phone/Kyf37SoftkeyBar.java',
      '        float[] weights =',
      '        if (getContext().getSystemService(android.app.KeyguardManager.class).isKeyguardLocked())\n'
      '            names = new String[]{"", "", "OK Unlock", ""}; // Keitai standby\n'
      '        float[] weights =',
      'Keitai standby')
print('Keitai SystemUI pass 2 staged')
