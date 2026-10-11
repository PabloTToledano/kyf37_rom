"""KYF37 stage 1: shared focus-colour theme + Clear/Back -> backspace rule (framework + SystemUI).

Idempotent; WSL Python 3.  Run AFTER fix-android10-keypad-panel.py (it rewrites Kyf37KeitaiKeys).
 * android.view.Kyf37FocusTheme   - palettes, Settings.Global kyf37_focus_theme observer, drawing
 * View.drawKyf37KeypadFocus      - now delegates to Kyf37FocusTheme (no yellow/navy any more)
 * android.view.Kyf37BackDel(+Policy) and ViewRootImpl.Kyf37BackDelStage
 * SystemUI Kyf37KeitaiKeys.selection() -> Kyf37FocusTheme.selection()
"""
from pathlib import Path
import re, shutil

WS = Path(__file__).resolve().parent
ROOT = Path('/home/pablo/kyf37-android10')
VIEWDIR = ROOT / 'frameworks/base/core/java/android/view'

def copy_sources():
    for name in ('Kyf37FocusTheme', 'Kyf37BackDelPolicy', 'Kyf37BackDel'):
        shutil.copy2(WS / (name + '.java.txt'), VIEWDIR / (name + '.java'))

def patch_view():
    p = VIEWDIR / 'View.java'
    s = p.read_text()
    if 'Kyf37FocusTheme.draw(this' in s:
        return 'View.java already delegates'
    a = s.index('    private android.graphics.Paint mKyf37FocusPaint;')
    b = s.index('    /**\n     * Draw any foreground content for this view.', a)
    s = s[:a] + ('    /** Selected-item look is owned by Kyf37FocusTheme (theme: Settings.Global kyf37_focus_theme). */\n'
                 '    private void drawKyf37KeypadFocus(Canvas canvas) {\n'
                 '        Kyf37FocusTheme.draw(this, canvas);\n'
                 '    }\n\n') + s[b:]
    p.write_text(s)
    return 'View.java now delegates to Kyf37FocusTheme'

STAGE = '''    /**
     * KYF37: the physical Clear key (BACK, scan 355) deletes a character when the focused
     * editable has text; with an empty field / no editor it stays a normal Back. Acts on key
     * release so the long-press (Memo pad, handled in PhoneWindowManager, which swallows the
     * release) is untouched. Auto-repeats are swallowed. The synthetic DEL pair goes through the
     * whole pipeline, so the IME (TT9) sees a normal backspace and clears its composing word.
     */
    final class Kyf37BackDelStage extends InputStage {
        private boolean mSwallowing;
        Kyf37BackDelStage(InputStage next) { super(next); }

        @Override
        protected int onProcess(QueuedInputEvent q) {
            if (!(q.mEvent instanceof KeyEvent)) return FORWARD;
            final KeyEvent e = (KeyEvent) q.mEvent;
            if (!Kyf37BackDelPolicy.isClearKey(e.getKeyCode(), e.getScanCode(),
                    SystemProperties.getBoolean("debug.kyf37.back_del_any", false))) {
                return FORWARD;
            }
            if (e.getAction() == KeyEvent.ACTION_DOWN) {
                if (e.getRepeatCount() == 0) {
                    mSwallowing = Kyf37BackDel.probe(mView) != Kyf37BackDelPolicy.NONE;
                }
                return mSwallowing ? FINISH_HANDLED : FORWARD;
            }
            if (!mSwallowing) return FORWARD;
            mSwallowing = false;
            if (e.isCanceled()) return FINISH_HANDLED;
            final int mode = Kyf37BackDel.probe(mView);
            if (mode == Kyf37BackDelPolicy.NONE) return FINISH_HANDLED;
            final int code = Kyf37BackDelPolicy.keyCodeFor(mode);
            final long now = SystemClock.uptimeMillis();
            enqueueInputEvent(new KeyEvent(now, now, KeyEvent.ACTION_DOWN, code, 0,
                    e.getMetaState(), e.getDeviceId(), 0, e.getFlags(), e.getSource()),
                    null, 0, false);
            enqueueInputEvent(new KeyEvent(now, now, KeyEvent.ACTION_UP, code, 0,
                    e.getMetaState(), e.getDeviceId(), 0, e.getFlags(), e.getSource()),
                    null, 0, false);
            return FINISH_HANDLED;
        }
    }

'''

def patch_viewroot():
    p = VIEWDIR / 'ViewRootImpl.java'
    s = p.read_text()
    if 'Kyf37BackDelStage' in s:
        return 'ViewRootImpl already patched'
    anchor = '    final class ViewPreImeInputStage extends InputStage {'
    assert s.count(anchor) == 1
    # keep the javadoc that precedes the class attached to it
    i = s.rfind('    /**', 0, s.index(anchor))
    s = s[:i] + STAGE + s[i:]
    old = '                mFirstInputStage = nativePreImeStage;'
    assert s.count(old) == 1
    s = s.replace(old, '                mFirstInputStage = new Kyf37BackDelStage(nativePreImeStage);')
    p.write_text(s)
    return 'ViewRootImpl: Kyf37BackDelStage first in the input pipeline'

def patch_systemui():
    p = ROOT / 'frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java'
    s = p.read_text()
    if 'Kyf37FocusTheme.selection' in s:
        return 'SystemUI already themed'
    s2 = re.sub(r'    private android\.graphics\.drawable\.Drawable selection\(View window\) \{.*?\n    \}\n',
                '    private android.graphics.drawable.Drawable selection(View window) {\n'
                '        return android.view.Kyf37FocusTheme.selection(window.getContext());\n    }\n',
                s, count=1, flags=re.S)
    assert s2 != s, 'selection() not found'
    p.write_text(s2)
    return 'SystemUI selections use Kyf37FocusTheme'

if __name__ == '__main__':
    copy_sources()
    for f in (patch_view, patch_viewroot, patch_systemui):
        print(f())
