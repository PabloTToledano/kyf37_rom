"""KYF37 keypad-nav v18 fix 1+3: visible Home selection and no stray status-bar outline. Idempotent; WSL Python 3.

Root causes (found on the v18 phone, see KEYPAD-NAV.md "v18 audit"):
 * Home grid cells are background-less LinearLayouts => PFLAG_SKIP_DRAW => View.draw(Canvas) is never
   called, so the Kyf37FocusTheme hook (drawKyf37KeypadFocus) never ran for the selected row. Cells now
   setWillNotDraw(false). Initial selection is posted after layout, Up/Down wrap at the grid edges.
 * Kyf37FocusTheme.draw outlined ANY focused view, including the one in the non-focusable status bar
   window (config_defaultInTouchMode=false gives it default focus). Focus outlines now require
   hasWindowFocus(); selected list rows (popup lists) keep drawing as before.
"""
from pathlib import Path
WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')
HOMES = [ROOT / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt']
THEMES = [ROOT / 'frameworks/base/core/java/android/view/Kyf37FocusTheme.java', WS / 'device-inspection/Kyf37FocusTheme.java.txt']

def sub(path, pairs):
    if not path.exists(): return
    s = path.read_text()
    o = s
    for old, new, marker in pairs:
        if marker in s: continue
        if old not in s:
            print('WARN anchor missing', path.name, old[:40]); continue
        s = s.replace(old, new, 1)
    if s != o:
        path.write_text(s); print('patched', path)

home_pairs = [
 ("            } else {\n                cell = (LinearLayout) convert;",
  "                cell.setWillNotDraw(false); // else View.draw() is skipped and the themed selection never paints\n"
  "            } else {\n                cell = (LinearLayout) convert;", 'cell.setWillNotDraw(false)'),
 ("        grid.requestFocus();\n        if (grid.getSelectedItemPosition() < 0) grid.setSelection(0);\n    }",
  "        grid.requestFocus();\n        if (grid.getSelectedItemPosition() < 0) grid.setSelection(0);\n"
  "        grid.post(new Runnable() { public void run() {\n"
  "            if (grid.getCount() > 0 && grid.getSelectedItemPosition() < 0) grid.setSelection(0);\n"
  "            grid.invalidate();\n        }});\n    }", 'grid.post(new Runnable() { public void run() {\n            if (grid.getCount()'),
 ("        if (event.getRepeatCount() == 0) {\n            if (code == KeyEvent.KEYCODE_CALL) {",
  "        int n = tiles.size(), sel = grid.getSelectedItemPosition();\n"
  "        if (n > 0 && sel >= 0) {\n"
  "            // GridView returns unhandled only at the edges: wrap around (keitai style).\n"
  "            if (code == KeyEvent.KEYCODE_DPAD_UP && sel < 3) { grid.setSelection(n - 1); return true; }\n"
  "            if (code == KeyEvent.KEYCODE_DPAD_DOWN && sel / 3 == (n - 1) / 3) { grid.setSelection(Math.min(sel % 3, n - 1)); return true; }\n"
  "        }\n"
  "        if (event.getRepeatCount() == 0) {\n            if (code == KeyEvent.KEYCODE_CALL) {", 'wrap around (keitai style)'),
]
for p in HOMES: sub(p, home_pairs)

theme_pairs = [
 ("        final boolean focus = v.isFocused() && !isContainer(v);",
  "        // A focused view in a window that does not hold window focus (status bar, overlays) is not\n"
  "        // where the user is: never outline it at rest.\n"
  "        final boolean focus = v.isFocused() && v.hasWindowFocus() && !isContainer(v);", 'v.hasWindowFocus()'),
]
for p in THEMES: sub(p, theme_pairs)
