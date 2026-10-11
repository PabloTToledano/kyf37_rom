#!/usr/bin/env python3
"""Make Settings secondary actions and list/header transitions keypad accessible."""
from pathlib import Path
root = Path('/home/pablo/kyf37-android10/packages/apps/Settings/src/com/android/settings')
p = root / 'widget/MasterSwitchPreference.java'
s = p.read_text()
anchor = '        mSwitch = (Switch) holder.findViewById(R.id.switchWidget);'
block = '''        // KYF37: the row opens details; Right selects the independent toggle.
        if (widgetView != null) {
            widgetView.setFocusable(true);
            widgetView.setContentDescription(getTitle());
            final View row = holder.itemView;
            row.setOnKeyListener((v, key, event) -> {
                if (key != android.view.KeyEvent.KEYCODE_DPAD_RIGHT) return false;
                if (event.getAction() == android.view.KeyEvent.ACTION_DOWN) {
                    widgetView.requestFocus();
                }
                return true;
            });
            widgetView.setOnKeyListener((v, key, event) -> {
                if (key != android.view.KeyEvent.KEYCODE_DPAD_LEFT) return false;
                if (event.getAction() == android.view.KeyEvent.ACTION_DOWN) row.requestFocus();
                return true;
            });
        }
'''
if '// KYF37: the row opens details' not in s:
    s = s.replace(anchor, block + anchor)
s = s.replace('            mSwitch.setContentDescription(getTitle());',
              '            mSwitch.setFocusable(false);\n            mSwitch.setContentDescription(getTitle());') if 'mSwitch.setFocusable(false)' not in s else s
p.write_text(s)
p = root / 'core/SettingsBaseActivity.java'
s = p.read_text()
block = '''    // KYF37: repair touch-only secondary actions after each dynamic bind.
    private void kyf37PrepareKeypad(View view, boolean clickableParent) {
        if (view.getVisibility() != View.VISIBLE) return;
        if (view.isClickable() && view.isEnabled() && !clickableParent) {
            view.setFocusable(true);
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); ++i) {
                kyf37PrepareKeypad(group.getChildAt(i), view.isClickable());
            }
        }
    }

    @Override
    public boolean dispatchKeyEvent(android.view.KeyEvent event) {
        View decor = getWindow().getDecorView();
        kyf37PrepareKeypad(decor, false);
        // RecyclerView consumes Up at its first row instead of leaving for the master bar.
        if (event.getKeyCode() == android.view.KeyEvent.KEYCODE_DPAD_UP) {
            View focus = getCurrentFocus();
            View child = focus;
            android.view.ViewParent parent = child == null ? null : child.getParent();
            while (parent instanceof ViewGroup) {
                ViewGroup group = (ViewGroup) parent;
                if (group instanceof androidx.recyclerview.widget.RecyclerView) {
                    androidx.recyclerview.widget.RecyclerView list =
                            (androidx.recyclerview.widget.RecyclerView) group;
                    boolean earlierTarget = false;
                    for (int i = 0; i < list.getChildCount(); ++i) {
                        View row = list.getChildAt(i);
                        if (row == child) break;
                        if (row.isEnabled() && row.hasFocusable()) earlierTarget = true;
                    }
                    if (!list.canScrollVertically(-1) && !earlierTarget) {
                        View bar = findViewById(R.id.switch_bar);
                        if (bar != null && bar.isShown() && bar.isEnabled()) {
                            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN) {
                                bar.requestFocus();
                            }
                            return true;
                        }
                    }
                    break;
                }
                child = group;
                parent = group.getParent();
            }
        }
        return super.dispatchKeyEvent(event);
    }

'''
anchor = '    @Override\n    public boolean onNavigateUp()'
if '// KYF37: repair touch-only' not in s:
    assert anchor in s
    s = s.replace(anchor, block + anchor)
else:
    begin = s.index('    // KYF37: repair touch-only')
    end = s.index(anchor, begin)
    s = s[:begin] + block + s[end:]
p.write_text(s)
 # No USB framework service is exposed on some live KYF37 builds. Keep the
 # connected-device page usable so Bluetooth controls remain reachable.
p = root / 'connecteddevice/usb/UsbBackend.java'
s = p.read_text()
s = s.replace('        List<UsbPort> ports = mUsbManager.getPorts();',
              '        if (mUsbManager == null) return; // KYF37: absent USB service\n'
              '        List<UsbPort> ports = mUsbManager.getPorts();') if 'KYF37: absent USB service' not in s else s
s = s.replace('return mUsbManager.getCurrentFunctions();',
              'return mUsbManager == null ? UsbManager.FUNCTION_NONE : mUsbManager.getCurrentFunctions();')
s = s.replace('return mUsbManager.getScreenUnlockedFunctions();',
              'return mUsbManager == null ? UsbManager.FUNCTION_NONE : mUsbManager.getScreenUnlockedFunctions();')
for name in ('setCurrentFunctions', 'setScreenUnlockedFunctions'):
    s = s.replace('        mUsbManager.' + name + '(functions);',
                  '        if (mUsbManager != null) mUsbManager.' + name + '(functions);')
p.write_text(s)
print('Settings keypad actions staged')
