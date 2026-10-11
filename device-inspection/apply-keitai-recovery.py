#!/usr/bin/env python3
"""Apply the KYF37 keitai recovery UI to the TWRP build tree (idempotent).

Run in WSL:  python3 /mnt/c/.../device-inspection/apply-keitai-recovery.py

What it does (all inside ~/kyf37-twrp, the dedicated TWRP tree, never the Android 10 tree):
  * copies gui/keymenu.cpp (new GUIKeyMenu object) and adds it to gui/Android.mk,
  * declares the class in gui/objects.hpp and registers <keymenu> in gui/pages.cpp,
  * TW_KYF37_KEITAI: no mouse cursor, no touch emulation, Clear(355)=Back,
    every key goes to PageManager::NotifyKey (no char translation),
  * installs the keitai theme as device/kyocera/kyf37/keitai-theme and selects it
    with TW_CUSTOM_THEME in BoardConfig.mk,
  * keeps the previous BoardConfig.mk as BoardConfig.mk.stock-theme.
"""
import re
import shutil
import sys
from pathlib import Path

HOST = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
SRC = HOST / 'device-inspection' / 'keitai-recovery'
ROOT = Path('/home/pablo/kyf37-twrp')
REC = ROOT / 'bootable/recovery'
DEV = ROOT / 'device/kyocera/kyf37'

changed = []

CONSOLE_KEY = r"""

// KYF37 keitai: Left/Right page through the console log (no touch screen).
int GUIConsole::NotifyKey(int key, bool down)
{
#ifdef TW_KYF37_KEITAI
	if (!down || mSlideout || !isConditionTrue())
		return 1;
	if (key != 105 /*KEY_LEFT*/ && key != 106 /*KEY_RIGHT*/)
		return 1;
	long rows = GetDisplayItemCount();
	long page = rows - 1 > 1 ? rows - 1 : 1;
	long n = (long)rConsole.size();
	long maxfirst = n - rows;
	if (maxfirst < 0) maxfirst = 0;
	long first = firstDisplayedItem + (key == 105 ? -page : page);
	if (first < 0) first = 0;
	if (first >= maxfirst) { first = maxfirst; scrollToEnd = true; } else { scrollToEnd = false; }
	firstDisplayedItem = first;
	y_offset = 0;
	scrollingSpeed = 0;
	mUpdate = 1;
	return 0;
#else
	return 1;
#endif
}
"""



def patch(path, edits, marker):
    s = path.read_text()
    if marker in s:
        return
    for old, new in edits:
        if old not in s:
            sys.exit('anchor missing in %s: %r' % (path, old[:60]))
        s = s.replace(old, new, 1)
    path.write_text(s)
    changed.append(str(path))


def main():
    assert REC.is_dir(), 'TWRP tree missing'
    # 1. new source file
    shutil.copyfile(SRC / 'gui/keymenu.cpp', REC / 'gui/keymenu.cpp')

    # 2. class declaration
    decl = (SRC / 'gui/keymenu_decl.inc').read_text()
    oh = REC / 'gui/objects.hpp'
    txt = oh.read_text()
    if 'class GUIKeyMenu' in txt:  # refresh an older declaration
        a = txt.index('// KYF37 keitai: cursor-less D-pad menu')
        b = txt.index('class GUIPartitionList : public GUIScrollList')
        if txt[a:b] != decl:
            oh.write_text(txt[:a] + decl + txt[b:])
            changed.append(str(oh))
    else:
        patch(oh, [('class GUIPartitionList : public GUIScrollList', decl + 'class GUIPartitionList : public GUIScrollList')], 'class GUIKeyMenu')

    # 3. build file + compile flag
    patch(REC / 'gui/Android.mk',
          [('    listbox.cpp \\\n', '    listbox.cpp \\\n    keymenu.cpp \\\n'),
           ('ifeq ($(TW_KYF37_DPAD),true)\nLOCAL_CFLAGS += -DTW_KYF37_DPAD\nendif\n',
            'ifeq ($(TW_KYF37_DPAD),true)\nLOCAL_CFLAGS += -DTW_KYF37_DPAD\nendif\n'
            'ifeq ($(TW_KYF37_KEITAI),true)\nLOCAL_CFLAGS += -DTW_KYF37_KEITAI\nendif\n')],
          'keymenu.cpp')

    # 4. object factory
    patch(REC / 'gui/pages.cpp',
          [('\t\telse if (type == "listbox")\n',
            '\t\telse if (type == "keymenu")\n\t\t{\n\t\t\tGUIKeyMenu* element = new GUIKeyMenu(child);\n'
            '\t\t\tmObjects.push_back(element);\n\t\t\tmRenders.push_back(element);\n\t\t\tmActions.push_back(element);\n\t\t}\n'
            '\t\telse if (type == "listbox")\n')],
          'type == "keymenu"')

    # 5. input: keitai mode replaces the cursor emulation
    patch(REC / 'gui/gui.cpp',
          [('#ifdef TW_KYF37_DPAD\n    if (ev.code == KEY_UP || ev.code == KEY_DOWN',
            '#ifdef TW_KYF37_KEITAI\n    // keitai UI: no cursor and no touch emulation. Physical Clear (355) is Back.\n'
            '    if (ev.code == 355) ev.code = KEY_BACK;\n'
            '#elif defined(TW_KYF37_DPAD)\n    if (ev.code == KEY_UP || ev.code == KEY_DOWN')],
          'TW_KYF37_KEITAI')

    # 6. no cursor
    mc = REC / 'gui/mousecursor.cpp'
    s = mc.read_text()
    if 'TW_KYF37_KEITAI' not in s:
        s = s.replace('#ifdef TW_KYF37_DPAD\n    m_present = true;', '#if defined(TW_KYF37_DPAD) && !defined(TW_KYF37_KEITAI)\n    m_present = true;', 1)
        s = s.replace('#ifndef TW_KYF37_DPAD\n    if (m_present != ev_has_mouse())', '#if !defined(TW_KYF37_DPAD) || defined(TW_KYF37_KEITAI)\n    if (m_present != ev_has_mouse())', 1)
        assert s.count('TW_KYF37_KEITAI') == 2, 'mousecursor anchors changed'
        mc.write_text(s)
        changed.append(str(mc))


    # 6b. keyed GUIAction objects honour their <condition> (stock ignores it for keys)
    patch(REC / 'gui/action.cpp',
          [('int GUIAction::NotifyKey(int key, bool down)\n{\n',
            'int GUIAction::NotifyKey(int key, bool down)\n{\n#ifdef TW_KYF37_KEITAI\n\tif (!isConditionTrue())\n\t\treturn 1;\n#endif\n')],
          'if (!isConditionTrue())\n\t\treturn 1;\n#endif')

    # 6c. console: Left/Right scroll the log with the D-pad
    patch(REC / 'gui/objects.hpp',
          [('\tvirtual int NotifyTouch(TOUCH_STATE state, int x, int y);\n\n\t// ScrollList interface\n',
            '\tvirtual int NotifyTouch(TOUCH_STATE state, int x, int y);\n\tvirtual int NotifyKey(int key, bool down);\n\n\t// ScrollList interface\n')],
          'virtual int NotifyKey(int key, bool down);\n\n\t// ScrollList interface')
    con = REC / 'gui/console.cpp'
    s2 = con.read_text()
    if 'GUIConsole::NotifyKey' not in s2:
        s2 += CONSOLE_KEY
        con.write_text(s2)
        changed.append(str(con))

    # 6d. Spanish strings for the keitai menus
    for lang, src in (('en', 'en-strings.xml'), ('es', 'es-strings.xml')):
        f = REC / ('gui/theme/common/languages/%s.xml' % lang)
        txt = f.read_text()
        if 'name="kb_install"' not in txt:
            strings = re.findall(r'<string name="[^"]+">.*?</string>', (SRC / src).read_text(), re.S)
            idx = txt.rfind('</resources>')
            f.write_text(txt[:idx] + '\n'.join(strings) + '\n' + txt[idx:])
            changed.append(str(f))
    es = REC / 'gui/theme/common/languages/es.xml'
    if False:
        txt = es.read_text()
        if 'name="kb_install"' not in txt:
            body = (SRC / 'es-strings.xml').read_text()
            strings = re.findall(r'<string name="[^"]+">.*?</string>', body, re.S)
            idx = txt.rfind('</resources>')
            es.write_text(txt[:idx] + '\n'.join(strings) + '\n' + txt[idx:])
            changed.append(str(es))

    # 7. keys must reach NotifyKey (digits, Enter) instead of char input
    patch(REC / 'gui/hardwarekeyboard.cpp',
          [('	int ch = KeyCodeToChar(key_code, shiftkey, ctrlkey);\n\n	if (ch != -1) {\n		mLastKeyChar = ch;\n		if (!PageManager::NotifyCharInput(ch))\n			return 1;',
            '	int ch = KeyCodeToChar(key_code, shiftkey, ctrlkey);\n#ifdef TW_KYF37_KEITAI\n	ch = -1; // keitai UI: digits/Enter are navigation keys, not text\n#endif\n\n	if (ch != -1) {\n		mLastKeyChar = ch;\n		if (!PageManager::NotifyCharInput(ch))\n			return 1;')],
          'TW_KYF37_KEITAI')


    # 9. HOST TEST hooks (only compiled with TW_KYF37_HOSTTEST=true on the make line; shipping builds ignore them)
    patch(REC / 'minuitwrp/graphics_fbdev.cpp',
          [('static GRSurface* fbdev_init(minui_backend* backend) {\n',
            'static GRSurface* fbdev_init(minui_backend* backend) {\n#ifdef TW_KYF37_HOSTTEST\n'
            '    gr_draw = (GRSurface*) calloc(1, sizeof(GRSurface));\n    gr_draw->width = 480; gr_draw->height = 854; gr_draw->pixel_bytes = 4;\n'
            '    gr_draw->row_bytes = 480 * 4; gr_draw->format = GGL_PIXEL_FORMAT_RGBX_8888;\n'
            '    gr_draw->data = (unsigned char*) calloc(854, 480 * 4);\n    return gr_draw;\n#endif\n'),
           ('static GRSurface* fbdev_flip(minui_backend* backend __unused) {\n',
            'static GRSurface* fbdev_flip(minui_backend* backend __unused) {\n#ifdef TW_KYF37_HOSTTEST\n'
            '    { FILE* f = fopen("/fb.raw.tmp", "wb"); if (f) { fwrite(gr_draw->data, 1, gr_draw->height * gr_draw->row_bytes, f); fclose(f); rename("/fb.raw.tmp", "/fb.raw"); }\n'
            '      return gr_draw; }\n#endif\n')],
          'TW_KYF37_HOSTTEST')
    patch(REC / 'minuitwrp/Android.mk',
          [('ifeq ($(TW_KYF37_DPAD),true)\nLOCAL_CFLAGS += -DTW_KYF37_DPAD\nendif\n',
            'ifeq ($(TW_KYF37_DPAD),true)\nLOCAL_CFLAGS += -DTW_KYF37_DPAD\nendif\n'
            'ifeq ($(TW_KYF37_HOSTTEST),true)\nLOCAL_CFLAGS += -DTW_KYF37_HOSTTEST\nendif\n')],
          'TW_KYF37_HOSTTEST')

    # 10. HOST TEST: pixelflinger's JIT needs /dev/ashmem, which does not exist under qemu-user.
    # The header defines TW_KYF37_HOSTTEST only when this script runs with --hosttest; shipping builds get an empty header.
    cut = ROOT / 'system/core/libcutils'
    patch(cut / 'ashmem-dev.c',
          [('#define ASHMEM_DEVICE\t"/dev/ashmem"\n',
            '#define ASHMEM_DEVICE\t"/dev/ashmem"\n#include <stdlib.h>\n#include "kyf37_hosttest.h"\n'),
           ('int ashmem_create_region(const char *name, size_t size)\n{\n\tint fd, ret;\n',
            'int ashmem_create_region(const char *name, size_t size)\n{\n\tint fd, ret;\n#ifdef TW_KYF37_HOSTTEST\n'
            '\t{ char p[] = "/tmp/ashmem-XXXXXX"; int f = mkstemp(p); if (f < 0) return f; unlink(p);\n'
            '\t  if (ftruncate(f, size) < 0) { close(f); return -1; } return f; }\n#endif\n')],
          'kyf37_hosttest.h')
    hdr = cut / 'kyf37_hosttest.h'
    want = '#define TW_KYF37_HOSTTEST 1\n' if '--hosttest' in sys.argv else '/* shipping build: no host test hooks */\n'
    if not hdr.exists() or hdr.read_text() != want:
        hdr.write_text(want)
        changed.append(str(hdr))

    # 8. theme + board config
    theme_dst = DEV / 'keitai-theme'
    if theme_dst.exists():
        shutil.rmtree(theme_dst)
    shutil.copytree(SRC / 'theme', theme_dst)
    changed.append(str(theme_dst))
    bc = DEV / 'BoardConfig.mk'
    s = bc.read_text()
    if 'TW_KYF37_KEITAI' not in s:
        shutil.copyfile(bc, DEV / 'BoardConfig.mk.stock-theme')
        s = s.rstrip('\n') + '\nTW_KYF37_KEITAI := true\nTW_CUSTOM_THEME := device/kyocera/kyf37/keitai-theme\n'
        bc.write_text(s)
        changed.append(str(bc))
    print('changed:', changed if changed else 'nothing (already applied)')


main()
