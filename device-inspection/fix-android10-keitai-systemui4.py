"""Keitai pass 4: legends follow keyguard state. Run in WSL after ...systemui3.py.

Softkey bar and shade guide only drew once, so "OK Unlock" stayed after unlocking. Both now
redraw twice a second while attached; the guide draws nothing while locked (the softkey bar
already says OK Unlock), keeping standby clean.
"""
from pathlib import Path

root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
java = root / 'src/com/android/systemui/statusbar/phone'

p = java / 'Kyf37SoftkeyBar.java'
s = p.read_text()
if 'keitaiTick' not in s:
    s = s.replace('    @Override protected void onAttachedToWindow() {\n        super.onAttachedToWindow();',
        '    private final Runnable keitaiTick = new Runnable() {\n'
        '        @Override public void run() { invalidate(); postDelayed(this, 500); }\n    };\n\n'
        '    @Override protected void onAttachedToWindow() {\n        super.onAttachedToWindow();\n        post(keitaiTick);', 1)
    s = s.replace('    @Override protected void onDetachedFromWindow() {',
        '    @Override protected void onDetachedFromWindow() {\n        removeCallbacks(keitaiTick);', 1)
    assert 'post(keitaiTick)' in s and 'removeCallbacks(keitaiTick)' in s
    p.write_text(s)

p = java / 'Kyf37KeitaiGuide.java'
s = p.read_text()
if 'keitaiTick' not in s:
    s = s.replace(' @Override protected void onDraw(Canvas canvas) {\n  super.onDraw(canvas);\n  boolean locked = getContext().getSystemService(KeyguardManager.class).isKeyguardLocked();',
        ' private final Runnable keitaiTick = new Runnable() {\n'
        '  @Override public void run() { invalidate(); postDelayed(this, 500); }\n };\n'
        ' @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); post(keitaiTick); }\n'
        ' @Override protected void onDetachedFromWindow() { removeCallbacks(keitaiTick); super.onDetachedFromWindow(); }\n'
        ' @Override protected void onDraw(Canvas canvas) {\n  super.onDraw(canvas);\n'
        '  boolean locked = getContext().getSystemService(KeyguardManager.class).isKeyguardLocked();\n'
        '  if (locked) return; // standby stays clean; the softkey bar says OK Unlock', 1)
    assert 'keitaiTick' in s
    p.write_text(s)
print('Keitai SystemUI pass 4 staged')
