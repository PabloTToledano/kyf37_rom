"""KYF37 keypad-nav v18 audit fixes (framework). Idempotent; WSL Python 3. Run after fix-android10-focus-theme.py.

1. Selected list rows are drawn by the list itself (AbsListView.dispatchDraw -> Kyf37FocusTheme.drawListRow), not by the
   child View hook: background-less row layouts (power menu, Home grid, many dialogs) are PFLAG_SKIP_DRAW so
   View.draw() never ran and the selected row stayed invisible. The View hook's "row" branch is removed (no double paint).
2. A focused plain view is outlined only if the user can act on it: clickable / long-clickable / text editor / seek bar /
   number picker / checkable. Default-focused non-interactive containers (status bar strip, notification shelf, scrims,
   whole header rows) are never outlined. Together with hasWindowFocus() (fix-android10-home-cursor.py) the status bar is
   highlighted only when it really holds window focus AND the focused view is an interactive control.
"""
from pathlib import Path
WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')
THEMES = [ROOT / 'frameworks/base/core/java/android/view/Kyf37FocusTheme.java',
          WS / 'device-inspection/Kyf37FocusTheme.java.txt']

for p in THEMES:
    if not p.exists():
        continue
    s = p.read_text()
    if 'drawListRow' in s:
        continue
    old = "        final boolean row = v.isSelected()\n                && v.getParent() instanceof android.widget.AbsListView;\n"
    assert old in s, p
    s = s.replace(old, "        final boolean row = false; // list rows are drawn by AbsListView (drawListRow)\n")
    old2 = "        final boolean focus = v.isFocused() && v.hasWindowFocus() && !isContainer(v);"
    assert old2 in s, p
    s = s.replace(old2, "        final boolean focus = v.isFocused() && v.hasWindowFocus() && !isContainer(v) && isInteractive(v);")
    helper = '''
    private static boolean isInteractive(View v) {
        return v.isClickable() || v.isLongClickable() || v.onCheckIsTextEditor()
                || v instanceof android.widget.AbsSeekBar || v instanceof android.widget.NumberPicker
                || v instanceof android.widget.Checkable || v instanceof android.widget.Spinner;
    }

    /** Called by AbsListView.dispatchDraw: paint the selected row (list focused, keypad mode). */
    public static void drawListRow(android.widget.AbsListView list, Canvas canvas, boolean show) {
        if (!show || !"kyf37".equals(Build.DEVICE)) return;
        final View sel = list.getSelectedView();
        if (sel == null || !sel.isEnabled() || sel.getVisibility() != View.VISIBLE) return;
        final float d = list.getResources().getDisplayMetrics().density;
        final int w = sel.getWidth(), h = sel.getHeight();
        if (w < 12 * d || h < 12 * d) return;
        watch(list.getContext());
        synchronized (sDrawn) { sDrawn.put(list, Boolean.TRUE); }
        sRect.set(sel.getLeft(), sel.getTop(), sel.getRight(), sel.getBottom());
        paintBox(canvas, sRect, d, sId);
    }
'''
    marker = "    private static boolean isContainer(View v) {"
    assert marker in s, p
    s = s.replace(marker, helper + "\n" + marker, 1)
    p.write_text(s)
    print('patched', p.name)

al = ROOT / 'frameworks/base/core/java/android/widget/AbsListView.java'
s = al.read_text()
if 'drawListRow' not in s:
    old = "        if (drawSelectorOnTop) {\n            drawSelector(canvas);\n        }\n"
    assert s.count(old) == 1
    s = s.replace(old, old + "        android.view.Kyf37FocusTheme.drawListRow(this, canvas, shouldShowSelector());\n")
    al.write_text(s)
    print('patched AbsListView')
