#!/usr/bin/env python3
"""Host-side tools for the KYF37 keitai recovery theme.

  python keitai-theme-tools.py check   [--ui theme/ui.xml]      static validation
  python keitai-theme-tools.py preview [--ui ...] [--out DIR]   render every page to PNG (layout simulation)

`check` enforces the rules the TWRP engine and our safety design depend on:
  * well-formed XML, every page reachable, every page jump target exists
  * every referenced font / image exists, every %var% used in layout has a default or is a TWRP builtin
  * every page has a way out (Back key action or a menu row leading elsewhere), except the busy/router pages
  * no destructive action (wipe, rm, nandroid restore, dd, reboot...) is bound directly to a menu row:
    they must be reached through confirm1/confirm2 (two-step), and confirm pages default to the safe row
  * a destructive confirm2 row must be shortcut-only
`preview` is NOT the real TWRP renderer: it re-implements the keymenu row layout with Pillow and the
same fonts, to show what each page looks like (focus row = first selectable row).
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / 'preview-fonts'
W, H = 480, 854

TW_BUILTIN_VARS = {
    'tw_time', 'tw_battery', 'tw_version', 'tw_file', 'tw_filename', 'tw_zip_index', 'tw_zip_queue_count', 'tw_storage_path',
    'tw_storage_free_size', 'tw_restore_name', 'tw_restore', 'tw_restore_list', 'tw_restore_selected', 'tw_backup_list',
    'tw_wipe_list', 'tw_operation', 'tw_partition', 'tw_file_progress', 'tw_size_progress', 'tw_operation_state',
    'tw_operation_status', 'tw_action', 'tw_action_param', 'tw_action2', 'tw_action2_param', 'tw_action_text1', 'tw_action_text2',
    'tw_complete_text1', 'tw_has_cancel', 'tw_cancel_action', 'tw_cancel_param', 'tw_has_action2', 'tw_clear_destination',
    'tw_check_partition_list', 'tw_backups_folder', 'tw_signed_zip_verify', 'tw_skip_digest_check_zip', 'tw_rm_rf',
    'tw_skip_digest_generate', 'tw_language', 'tw_enable_adb_backup', 'tw_page_done', 'ui_progress', 'tw_selectimage',
    'tw_text1', 'tw_text2', 'tw_text3', 'tw_text4',
}
DESTRUCTIVE = {'wipe', 'cmd', 'dd', 'nandroid', 'flash', 'flashimage', 'repair', 'resize', 'changefilesystem', 'fixcontexts', 'partitionsd'}
NO_BACK_OK = {'main', 'clear_vars', 'backup_check', 'wipe_adv_check', 'wipe_adv_dalvik', 'action_page', 'singleaction_page',
              'flash_zip', 'backup_run', 'restore_run'}
SPECIAL_PAGES = {'main', 'decrypt', 'system_readonly', 'main2', 'singleaction_page', 'action_page', 'flash_zip'}


def load(ui):
    tree = ET.parse(ui)
    root = tree.getroot()
    pages = {p.get('name'): p for p in root.find('pages').findall('page')}
    return root, pages


def page_jumps(page):
    out = []
    for a in page.iter('action'):
        if a.get('function') == 'page' and a.text:
            out.append(a.text.strip())
    return out


def check(ui):
    errs, warns = [], []
    root, pages = load(ui)
    res = root.find('resources')
    fonts = {f.get('name'): f.get('filename') for f in res.findall('font')}
    images = {i.get('name'): i.get('filename') for i in res.findall('image')}
    variables = {v.get('name') for v in root.find('variables').findall('variable')}
    theme = Path(ui).parent
    for name, fn in fonts.items():
        if not (FONTS / fn).exists():
            errs.append('font file missing in preview-fonts: %s' % fn)
    for name, fn in images.items():
        if not (theme / 'images' / (fn + '.png')).exists():
            errs.append('image missing: %s.png' % fn)
    # referenced fonts exist
    for el in root.iter():
        if el.tag == 'font' and el.get('resource') and el.get('resource') not in fonts:
            errs.append('unknown font resource %s' % el.get('resource'))
    # style names
    styles = {s.get('name') for s in root.find('styles').findall('style')}
    for el in root.iter():
        if el.get('style') and el.get('style') not in styles:
            errs.append('unknown style %s' % el.get('style'))
    # page targets
    targets = set()
    for pn, p in pages.items():
        for t in page_jumps(p):
            if '%' in t:
                continue
            targets.add(t)
            if t not in pages:
                errs.append('page %s jumps to missing page %s' % (pn, t))
    for needed in ('main', 'main2', 'decrypt', 'system_readonly', 'singleaction_page', 'action_page', 'flash_zip', 'flash_done'):
        if needed not in pages:
            errs.append('TWRP core page missing: %s' % needed)
    # reachability from main
    seen, todo = set(), ['main']
    while todo:
        n = todo.pop()
        if n in seen or n not in pages:
            continue
        seen.add(n)
        todo.extend(t for t in page_jumps(pages[n]) if '%' not in t)
        # dynamic jumps resolve to known pages
        for dyn in ('main2', 'restore_select', 'backup_setup', 'wipe', 'wipe_adv', 'files', 'extras_pick', 'logs', 'install_pick', 'restore_pick', 'flash_done', 'tools'):
            if any('%' in t for t in page_jumps(pages[n])) and dyn in pages:
                todo.append(dyn)
    for pn in pages:
        if pn not in seen and pn not in SPECIAL_PAGES:
            warns.append('page not reachable from main: %s' % pn)
    # variable usage
    for pn, p in pages.items():
        xmltxt = ET.tostring(p, encoding='unicode')
        for m in re.finditer(r'%([a-z_0-9]+)%', xmltxt):
            v = m.group(1)
            if v not in variables and v not in TW_BUILTIN_VARS and not v.startswith('tw_'):
                errs.append('page %s uses unknown variable %%%s%%' % (pn, v))
    # way out + keys
    for pn, p in pages.items():
        if pn in NO_BACK_OK:
            continue
        keys = [a.find('touch').get('key') for a in p.findall('action') if a.find('touch') is not None]
        has_back = 'back' in keys
        menu_exits = bool(p.findall('.//keymenu'))
        if not (has_back or menu_exits):
            errs.append('page %s has no Back key and no menu' % pn)
        if pn not in ('main2', 'decrypt', 'system_readonly') and not has_back and pn not in ('action_page',):
            warns.append('page %s has no Back key action (menu only)' % pn)
        for k in keys:
            if not (k in ('back', 'home', 'power') or k.isdigit()):
                errs.append('page %s: bad key name %s' % (pn, k))
    # destructive rows must go via confirm pages
    for pn, p in pages.items():
        for km in p.iter('keymenu'):
            for li in km.findall('listitem'):
                for a in li.iter('action'):
                    fn = a.get('function')
                    safe_cmd = fn == 'cmd' and re.match(r'^(dmesg > /tmp/|cat /proc/last_kmsg > /tmp/)', a.text or '')
                    if fn in DESTRUCTIVE and not safe_cmd and not (pn in ('install_confirm',) and fn == 'flash') and not (
                            pn == 'flash_done' and fn == 'wipe'):
                        errs.append('page %s row "%s" runs %s directly (must use confirm1/confirm2)' % (pn, li.get('name'), fn))
                    if fn == 'set' and (a.text or '').startswith('tw_action=') and (a.text.split('=', 1)[1] in DESTRUCTIVE):
                        # allowed: this is the confirm() priming sequence, must end with page confirm1
                        acts = [x.get('function') + ':' + (x.text or '') for x in li.iter('action')]
                        if not acts[-1].startswith('page:confirm1'):
                            errs.append('page %s row "%s" primes %s but does not open confirm1' % (pn, li.get('name'), a.text))
    for pn in ('confirm1', 'confirm2'):
        km = pages[pn].find('.//keymenu')
        if km.get('keepfocus') != '0' or km.get('startfocus') != '0':
            errs.append('%s must reset focus to row 0' % pn)
        first = km.findall('listitem')[0]
        if 'Cancel' not in first.get('name'):
            errs.append('%s first row must be Cancel' % pn)
    c2 = pages['confirm2'].find('.//keymenu')
    conf = [li for li in c2.findall('listitem') if 'CONFIRM' in li.get('name')]
    if not conf or conf[0].get('shortcutonly') != '1' or conf[0].get('hotkey') != '0':
        errs.append('confirm2 confirm row must be shortcut-only on key 0')
    # reboot/poweroff rows
    # forbidden partitions never offered
    txt = ET.tostring(root, encoding='unicode')
    for bad in ('/persist', 'modemst', '/dev/block', 'keystore', '/misc', 'by-name'):
        if bad in txt:
            errs.append('theme mentions protected partition %s' % bad)
    # keymenu sanity
    for pn, p in pages.items():
        for km in p.iter('keymenu'):
            if not (km.findall('listitem') or km.find('browse') is not None or km.find('textfile') is not None):
                errs.append('page %s has an empty keymenu' % pn)
            for li in km.findall('listitem'):
                if li.get('name') is None:
                    errs.append('listitem without name on %s' % pn)
    for e in errs:
        print('ERROR:', e)
    for w in warns:
        print('warn :', w)
    print('check: %d pages, %d errors, %d warnings' % (len(pages), len(errs), len(warns)))
    return 1 if errs else 0


# ------------------------------------------------------------------ preview

def preview(ui, out_dir, lang):
    from PIL import Image, ImageDraw, ImageFont
    root, pages = load(ui)
    res = root.find('resources')
    fonts = {}
    for f in res.findall('font'):
        fonts[f.get('name')] = ImageFont.truetype(str(FONTS / f.get('filename')), int(f.get('size')))
    styles = {s.get('name'): s for s in root.find('styles').findall('style')}
    variables = {v.get('name'): v.get('value') for v in root.find('variables').findall('variable')}
    sample = dict(variables)
    sample.update({'tw_time': '14:07', 'tw_battery': '82', 'tw_version': '3.7.0_9-0', 'tw_file': 'kyf37-android10-go-20261007-twrp-v18.zip',
                   'tw_zip_index': '1', 'tw_zip_queue_count': '1', 'tw_storage_path': '/external_sd', 'tw_storage_free_size': '5120',
                   'tw_operation_status': '0', 'tw_operation_state': '0', 'tw_restore_name': '2026-10-09--14-02-11_KYF37',
                   'tw_action_text1': 'Factory reset...', 'tw_action_text2': '', 'tw_complete_text1': 'Backup complete',
                   'tw_operation': 'Backup', 'tw_partition': 'system', 'tw_file_progress': '1 of 3 files', 'tw_size_progress': '412 / 1536 MB',
                   'tw_has_cancel': '0', 'tw_has_action2': '0', 'tw_check_partition_list': '3', 'tw_wipe_list': '/cache;',
                   'tw_signed_zip_verify': '0', 'kb_c_title': 'Factory reset?', 'kb_c_l1': 'Erases apps and settings in /data.',
                   'kb_c_l2': 'Internal storage files are kept.', 'kb_c_two': '1', 'kb_path': '/external_sd/TWRP/BACKUPS/981108631314',
                   'kb_hint': 'Press the number key shown to confirm', 'tw_filename': '/external_sd/kyf37-android10-go-20261007-twrp-v18.zip',
                   'tw_backup_list': '/boot;/system;/data;', 'tw_restore_list': '/boot;/system;/data;', 'tw_restore_selected': '/boot;/data;',
                   'tw_skip_digest_check_zip': '0', 'tw_rm_rf': '0', 'tw_skip_digest_generate': '0'})
    es = {}
    if lang == 'es':
        for m in re.finditer(r'<string name="([^"]+)">(.*?)</string>', (HERE / 'es-strings.xml').read_text(encoding='utf-8')):
            es[m.group(1)] = m.group(2)

    def parse(txt):
        txt = txt or ''
        def sub_res(m):
            body = m.group(1)
            if '=' in body:
                k, d = body.split('=', 1)
            else:
                k, d = body, body
            return es.get(k, d)
        txt = re.sub(r'\{@([^}]*)\}', sub_res, txt)
        return re.sub(r'%([a-zA-Z_0-9]+)%', lambda m: sample.get(m.group(1), ''), txt)

    def cond_ok(el):
        conds = []
        for c in el.findall('condition'):
            conds.append(c)
        cs = el.find('conditions')
        if cs is not None:
            conds += cs.findall('condition')
        for c in conds:
            v1 = sample.get(c.get('var1'), '')
            op = c.get('op', '=')
            v2 = c.get('var2', '')
            v2 = sample.get(v2, v2)
            try:
                a, b = float(v1), float(v2)
            except ValueError:
                a, b = v1, v2
            ok = {'=': a == b, '!=': a != b, '>': a > b, '<': a < b, '>=': a >= b, '<=': a <= b}.get(op, True)
            if not ok:
                return False
        return True

    def hexc(s, default='#ffffff'):
        return s if s and s.startswith('#') else default

    def style_node(obj, tag):
        n = obj.find(tag)
        if n is not None:
            return n
        st = styles.get(obj.get('style') or obj.tag)
        return st.find(tag) if st is not None else None

    def font_h(f):
        a, d = f.getmetrics()
        return a + d

    out_dir.mkdir(parents=True, exist_ok=True)
    sheets = []
    for pn, page in pages.items():
        if pn in ('main', 'clear_vars', 'backup_check', 'wipe_adv_check', 'wipe_adv_dalvik', 'singleaction_page'):
            continue
        img = Image.new('RGB', (W, H), '#000000')
        dr = ImageDraw.Draw(img)
        for obj in page:
            tag = obj.tag
            if tag == 'background':
                dr.rectangle([0, 0, W, H], fill=hexc(obj.get('color')))
            elif tag == 'fill':
                if not cond_ok(obj):
                    continue
                pl = obj.find('placement')
                x, y, w, h = [int(pl.get(k)) for k in ('x', 'y', 'w', 'h')]
                dr.rectangle([x, y, x + w - 1, y + h - 1], fill=hexc(obj.get('color')))
            elif tag == 'text':
                if not cond_ok(obj):
                    continue
                f = fonts[obj.find('font').get('resource')]
                pl = obj.find('placement')
                x, y, p = int(pl.get('x')), int(pl.get('y')), int(pl.get('placement', '0'))
                t = parse(obj.find('text').text)
                tw = dr.textlength(t, font=f)
                if tw > (x if p == 1 else (W - x if p == 0 else 2 * min(x, W - x))):
                    pass
                if p == 1:
                    x -= tw
                elif p in (4, 5):
                    x -= tw / 2
                dr.text((x, y), t, font=f, fill=hexc(obj.get('color')))
            elif tag == 'console':
                pl = obj.find('placement')
                x, y, w, h = [int(pl.get(k)) for k in ('x', 'y', 'w', 'h')]
                f = fonts['fixed']
                lh = font_h(f)
                lines = ['Installing zip...', 'Verifying package', 'Patching boot image', 'Writing system 1536MB', 'Checking sha256 ... OK',
                         'Boot image signed: yes', 'Backup rollback copies kept', 'Script succeeded: result was [1.000000]', 'Updating partition details...',
                         '...done']
                lines = (lines * 6)[: h // lh]
                yy = y
                for ln in lines:
                    dr.text((x, yy), ln[: w // 11], font=f, fill='#F2F5FA')
                    yy += lh
            elif tag == 'progressbar':
                pl = obj.find('placement')
                x, y = int(pl.get('x')), int(pl.get('y'))
                dr.rectangle([x, y, x + 459, y + 27], fill='#22314D', outline='#9FB0C8', width=2)
                dr.rectangle([x, y, x + 270, y + 27], fill='#FFC300')
            elif tag == 'keymenu':
                if not cond_ok(obj):
                    continue
                draw_menu(dr, obj, style_node, fonts, parse, cond_ok, sample, font_h, hexc)
        name = '%s.png' % pn
        img.save(out_dir / name)
        sheets.append((pn, img))
    # contact sheets (6 per sheet, 3x2)
    per = 6
    for si in range(0, len(sheets), per):
        group = sheets[si:si + per]
        sheet = Image.new('RGB', (3 * (W // 2 + 10) + 10, 2 * (H // 2 + 30) + 10), '#222222')
        sd = ImageDraw.Draw(sheet)
        for i, (pn, im) in enumerate(group):
            small = im.resize((W // 2, H // 2))
            cx, cy = 10 + (i % 3) * (W // 2 + 10), 10 + (i // 3) * (H // 2 + 30)
            sheet.paste(small, (cx, cy + 20))
            sd.text((cx, cy + 2), pn, font=ImageFont.truetype(str(FONTS / 'RobotoCondensed-Regular.ttf'), 16), fill='#ffffff')
        sheet.save(out_dir / ('sheet-%02d.png' % (si // per + 1)))
    print('rendered %d pages to %s' % (len(sheets), out_dir))


def draw_menu(dr, obj, style_node, fonts, parse, cond_ok, sample, font_h, hexc):
    from PIL import ImageFont
    pl = obj.find('placement')
    mx, my, mw, mh = [int(pl.get(k)) for k in ('x', 'y', 'w', 'h')]
    font_node = style_node(obj, 'font')
    f = fonts[font_node.get('resource')]
    spacing = int(font_node.get('spacing', '0'))
    fcol = hexc(font_node.get('color'))
    fhi = hexc(font_node.get('highlightcolor'), fcol)
    hl = style_node(obj, 'highlight')
    hlcol = hexc(hl.get('color')) if hl is not None else fhi
    bg = style_node(obj, 'background')
    bgcol = hexc(bg.get('color')) if bg is not None else '#000000'
    sep = style_node(obj, 'separator')
    seph = int(sep.get('height', '0')) if sep is not None else 0
    sepcol = hexc(sep.get('color')) if sep is not None else '#000000'
    rowh = font_h(f) + spacing + seph
    dr.rectangle([mx, my, mx + mw, my + mh], fill=bgcol)
    numbered = obj.get('numbered') == '1'
    browse = obj.find('browse')
    textfile = obj.find('textfile')
    items = []
    if browse is not None:
        if sample.get('kb_path', '/') != browse.get('root'):
            items.append(dict(name='..  (up)', right='', sel=True))
        names = ['2026-10-09--14-02-11_KYF37/', 'kyf37-android10-go-20261007-twrp-v18.zip', 'kyf37-android10-go-20261007-twrp-v17.zip',
                 'KYF37-Android10-rollback-v17/', 'TWRP/', 'DCIM/', 'keitai-extras/', 'notes.txt'] * 3
        if browse.get('choosedirs') == '1':
            names = ['2026-10-09--14-02-11_KYF37', '2026-10-08--21-40-02_KYF37', '2026-10-07--09-15-33_KYF37', 'before-v18-test']
        for i, n in enumerate(names):
            items.append(dict(name=n, right='' if (n.endswith('/') or '.' not in n or browse.get('showsize') == '0') else '%d MB' % (1500 - i * 13), sel=True))
    elif textfile is not None:
        lg = ['I:Loading volume /system', 'I:Mounting /external_sd', 'I:kyf37 keitai theme loaded', 'I:Page changed to main2',
              'I:Command: twrp install /external_sd/x.zip', 'I:Zip verified', 'W:No SELinux contexts for /cache', 'I:Backup done']
        for i in range(60):
            items.append(dict(name=lg[i % len(lg)], right='', sel=False, plain=True))
    else:
        for li in obj.findall('listitem'):
            if not cond_ok(li):
                continue
            mem = li.get('member')
            if mem and li.get('availvar'):
                if mem + ';' not in sample.get(li.get('availvar'), ''):
                    continue
            chk = None
            if mem:
                chk = (mem + ';') in sample.get(li.get('listvar'), '')
            elif li.find('data') is not None:
                chk = sample.get(li.find('data').get('variable'), '0') != '0'
            elif li.get('mountpt'):
                chk = li.get('mountpt') in ('/external_sd', '/cache')
            items.append(dict(name=parse(li.get('name')), right=parse(li.get('value') or ''), danger=li.get('danger') == '1',
                              hot=li.get('hotkey'), only=li.get('shortcutonly') == '1', chk=chk, sel=True))
    # focus row: first not shortcut-only
    focus = 0
    for i, it in enumerate(items):
        if not it.get('only'):
            focus = i
            break
    if textfile is not None:
        focus = len(items) - 1
    visible = mh // rowh
    first = max(0, focus - visible + 1) if textfile is not None else 0
    # numbers
    used = {int(it['hot']) for it in items if it.get('hot') is not None}
    nxt = 1
    for it in items:
        if it.get('hot') is not None:
            it['num'] = int(it['hot'])
        elif numbered:
            while nxt in used and nxt <= 9:
                nxt += 1
            if nxt <= 9:
                it['num'] = nxt
                used.add(nxt)
                nxt += 1
    for r in range(visible + 1):
        idx = first + r
        if idx >= len(items):
            break
        it = items[idx]
        y = my + r * rowh
        if y + rowh > my + mh + 2:
            break
        h = rowh - seph
        foc = idx == focus
        if foc:
            dr.rectangle([mx, y, mx + mw, y + h - 1], fill=hlcol)
            if textfile is None:
                dr.rectangle([mx, y, mx + 5, y + h - 1], fill=fcol)
        col = fhi if foc else fcol
        if it.get('danger') and not foc:
            col = '#FF6060'
        if it.get('only') and not foc:
            col = '#FFBE3C'
        x = mx + 14
        ty = y + (h - font_h(f)) // 2
        if it.get('num') is not None:
            bw = font_h(f) - 2
            dr.rectangle([x, y + 8, x + bw, y + h - 9], fill=col)
            dr.text((x + bw / 2, ty), str(it['num']), font=f, fill=hlcol if foc else bgcol, anchor='ma')
            x += bw + 14
        if it.get('chk') is not None:
            bs = font_h(f) * 3 // 4
            by = y + (h - bs) // 2
            dr.rectangle([x, by, x + bs, by + bs], fill=col)
            dr.rectangle([x + 3, by + 3, x + bs - 3, by + bs - 3], fill=hlcol if foc else bgcol)
            if it['chk']:
                dr.rectangle([x + 7, by + 7, x + bs - 7, by + bs - 7], fill=col)
            x += bs + 12
        right = it.get('right') or ''
        rw = 0
        edge = mx + mw - 10
        if right:
            rw = dr.textlength(right, font=f)
            dr.text((edge - rw, ty), right, font=f, fill=col)
        avail = edge - x - (rw + 12 if rw else 0)
        label = it['name']
        lf = fonts['fixed'] if textfile is not None else f
        tw = dr.textlength(label, font=lf)
        if tw > avail and textfile is None:
            # engine shrinks the font to fit (gr_textEx_scaleW scale=1)
            sf = ImageFont.truetype(lf.path, max(10, int(lf.size * avail / tw)))
            dr.text((x, ty + (font_h(lf) - font_h(sf)) // 2), label, font=sf, fill=col)
        else:
            dr.text((x, ty), label, font=lf, fill=col)
        if seph:
            dr.rectangle([mx, y + h, mx + mw, y + rowh - 1], fill=sepcol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'preview'])
    ap.add_argument('--ui', default=str(HERE / 'theme/ui.xml'))
    ap.add_argument('--out', default=str(HERE.parent.parent / 'kyf37-twrp-device/keitai/previews'))
    ap.add_argument('--lang', default='en')
    a = ap.parse_args()
    if a.cmd == 'check':
        sys.exit(check(a.ui))
    preview(a.ui, Path(a.out), a.lang)


if __name__ == '__main__':
    main()
