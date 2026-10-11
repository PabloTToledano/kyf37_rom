#!/usr/bin/env python3
"""Generate the KYF37 keitai recovery theme (theme/ui.xml, splash.xml, images, es strings).

Run on the host (needs Pillow for the two progress-bar images):
    python device-inspection/keitai-recovery/build-keitai-theme.py

Output goes to device-inspection/keitai-recovery/theme/ and es-strings.xml.
Everything is generated from this file, so adding a menu row is a one-line edit
(see EXTRAS near the bottom for the documented extension point).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'theme'
W, H = 480, 854

C = dict(bg='#0B1220', bar='#1B3B6F', text='#F2F5FA', muted='#9FB0C8', accent='#FFC300',
         danger='#FF6B6B', ok='#6BE675', foot='#05080E', line='#22314D', dark='#101010')

STRINGS = {}     # key -> (en, es)
ES = {}          # key -> es text


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


_used_keys = set()


def tr(key, en, es=None):
    """Return a TWRP {@key=English} reference and remember the Spanish text."""
    if key in _used_keys and STRINGS[key][0] != en:
        sys.exit('duplicate key with different text: ' + key)
    _used_keys.add(key)
    STRINGS[key] = (en, es)
    return '{@%s=%s}' % (key, en)


def cond_xml(conds):
    if not conds:
        return ''
    if isinstance(conds, tuple):
        conds = [conds]
    def one(c):
        v1, op, v2 = c
        opx = '' if op == '=' else ' op="%s"' % esc(op)
        return '<condition var1="%s"%s var2="%s"/>' % (v1, opx, esc(str(v2)))
    if len(conds) == 1:
        return one(conds[0])
    return '<conditions>' + ''.join(one(c) for c in conds) + '</conditions>'


def action_xml(acts, tag='actions'):
    if not acts:
        return ''
    out = '<%s>' % tag
    for a in acts:
        if isinstance(a, str):
            out += '<action function="%s"/>' % a
        else:
            fn, arg = a
            out += '<action function="%s">%s</action>' % (fn, esc(arg))
    return out + '</%s>' % tag


def TEXT(x, y, text, font='font_m', color=None, placement=0, cond=None, w=None):
    color = color or C['text']
    wattr = ' w="%d"' % w if w else ''
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ('<text color="%s"><font resource="%s"/><placement x="%d" y="%d"%s placement="%d"/>%s<text>%s</text></text>'
            % (color, font, x, y, wattr, placement, cond_xml(cond), text))


def FILL(x, y, w, h, color, cond=None):
    return '<fill color="%s">%s<placement x="%d" y="%d" w="%d" h="%d"/></fill>' % (color, cond_xml(cond), x, y, w, h)


def KEY(key, acts, cond=None):
    return '<action><touch key="%s"/>%s%s</action>' % (key, cond_xml(cond), action_xml(acts))


def ON_ENTER(acts, cond=None):
    return '<action>%s%s</action>' % (cond_xml(cond), action_xml(acts))


# ---------------------------------------------------------------- footer / chrome

def footer(kind):
    s = FILL(0, 778, W, 2, C['accent']) + FILL(0, 780, W, 74, C['foot'])
    y = 802
    if kind == 'nav':
        s += TEXT(14, y, tr('kb_f_menu', 'F1 Menu', 'F1 Menu'), 'font_hint', C['muted'])
        s += TEXT(240, y, tr('kb_f_ok', 'OK Select', 'OK Elegir'), 'font_hint', C['accent'], 5)
        s += TEXT(466, y, tr('kb_f_back', 'Back (Clear)', 'Atras (Clear)'), 'font_hint', C['muted'], 1)
    elif kind == 'view':
        s += TEXT(14, y, tr('kb_f_menu', 'F1 Menu', 'F1 Menu'), 'font_hint', C['muted'])
        s += TEXT(240, y, tr('kb_f_scroll', 'Up/Dn  </> page', 'Arr/Ab  </> pag.'), 'font_hint', C['accent'], 5)
        s += TEXT(466, y, tr('kb_f_back', 'Back (Clear)', 'Atras (Clear)'), 'font_hint', C['muted'], 1)
    elif kind == 'busy':
        s += TEXT(240, y, tr('kb_f_busy', 'Working - please wait  (</> scroll log)', 'Trabajando - espere  (</> desplaza)'), 'font_hint', C['accent'], 5)
    elif kind == 'cancel':
        s += TEXT(14, y, tr('kb_f_busy2', 'Working...', 'Trabajando...'), 'font_hint', C['muted'])
        s += TEXT(466, y, tr('kb_f_cancel', 'Back = Cancel', 'Atras = Cancelar'), 'font_hint', C['danger'], 1)
    return s


def chrome(titles, info=None, foot='nav'):
    """titles: list of (text, color, cond)."""
    s = '<background color="%s"/>' % C['bg']
    s += FILL(0, 0, W, 64, C['bar'])
    for text, color, cond in titles:
        s += TEXT(16, 12, text, 'font_t', color or C['text'], 0, cond)
    s += TEXT(466, 22, '%tw_time%  ' + tr('kb_bat', 'Bat %tw_battery%', 'Bat %tw_battery%'), 'font_s', '#C9D6EA', 1)
    if info:
        s += TEXT(16, 74, info, 'font_s', C['muted'], 0)
    s += footer(foot)
    return s


def nav_keys(back=None, home=True):
    s = ''
    if back:
        s += KEY('back', [('page', back)]) + KEY('60', [('page', back)])
    if home:
        s += KEY('59', [('page', 'main')]) + KEY('116', [('page', 'main')])
    s += KEY('254', ['screenshot'])
    return s


# ---------------------------------------------------------------- widgets

def item(label, acts=None, value=None, danger=False, hotkey=None, shortcutonly=False, member=None,
         listvar=None, availvar=None, mountpt=None, var=None, cond=None):
    a = ''
    if value:
        a += ' value="%s"' % esc(value)
    if danger:
        a += ' danger="1"'
    if hotkey is not None:
        a += ' hotkey="%d"' % hotkey
    if shortcutonly:
        a += ' shortcutonly="1"'
    if member:
        a += ' member="%s" listvar="%s"' % (member, listvar)
        if availvar:
            a += ' availvar="%s"' % availvar
    if mountpt:
        a += ' mountpt="%s"' % mountpt
    inner = cond_xml(cond)
    if var:
        inner += '<data variable="%s"/>' % var
    inner += action_xml(acts)
    return '<listitem name="%s"%s>%s</listitem>' % (esc(label), a, inner)


def KEYMENU(items, y=104, h=674, numbered=True, keepfocus=True, startfocus=0, paging=True, cond=None,
            browse=None, textfile=None, style='keymenu'):
    attrs = ' style="%s"' % style
    attrs += ' numbered="%d" keepfocus="%d" startfocus="%d" paging="%d"' % (numbered, keepfocus, startfocus, paging)
    s = '<keymenu%s>%s<placement x="0" y="%d" w="%d" h="%d"/>' % (attrs, cond_xml(cond), y, W, h)
    if browse:
        s += browse
    if textfile:
        s += textfile
    s += ''.join(items)
    return s + '</keymenu>'


def BROWSE(path, root, flt, acts, pathvar='kb_path', filevar='tw_filename', selvar='tw_file',
           choosedirs=False, reverse=False, rootvar=None, showsize=True):
    a = 'path="%s" root="%s" filter="%s" pathvar="%s" filevar="%s" selvar="%s" choosedirs="%d" reverse="%d" showsize="%d"' % (
        path, root, flt, pathvar, filevar, selvar, choosedirs, reverse, showsize)
    if rootvar:
        a += ' rootvar="%s"' % rootvar
    return '<browse %s>%s</browse>' % (a, action_xml(acts))


def CONSOLE(y, h, arrows=False):
    return ('<console style="console"><placement x="8" y="%d" w="%d" h="%d"/></console>' % (y, W - 16, h)
            + FILL(8, y - 2, W - 16, 2, C['line']) + FILL(8, y + h, W - 16, 2, C['line']))


def PROGRESS(y):
    return ('<progressbar><placement x="10" y="%d"/><resource empty="progress_empty" full="progress_full"/>'
            '<data name="ui_progress"/></progressbar>' % y)


pages = []


def PAGE(name, *parts):
    pages.append('<page name="%s">%s</page>' % (name, ''.join(parts)))


def menu_page(name, title, items, back='main2', info=None, foot='nav', **kw):
    PAGE(name, chrome([(title, None, None)], info, foot), nav_keys(back), KEYMENU(items, **kw))


def goto(page, *pre):
    return list(pre) + [('page', page)]


def set_(var, val):
    return ('set', '%s=%s' % (var, val))


def confirm(title_key_en, lines, fn, arg, back, two, done_text, run_text, danger=True, extra=None):
    """Actions that prime the generic confirmation pages and open them."""
    acts = [set_('kb_c_title', title_key_en), set_('kb_c_l1', lines[0] if len(lines) > 0 else ''),
            set_('kb_c_l2', lines[1] if len(lines) > 1 else ''), set_('kb_c_l3', lines[2] if len(lines) > 2 else ''),
            set_('kb_c_back', back), set_('kb_c_two', '1' if two else '0'),
            set_('tw_action', fn), set_('tw_action_param', arg), set_('tw_has_action2', '0'),
            set_('tw_action_text1', run_text), set_('tw_action_text2', ''),
            set_('tw_complete_text1', done_text), set_('tw_has_cancel', '0')]
    if extra:
        acts += extra
    acts.append(('page', 'confirm1'))
    return acts


# ---------------------------------------------------------------- pages

def build_pages():
    # --- start router (clears operation state) --------------------------------
    PAGE('main', ON_ENTER([set_('tw_clear_destination', 'main2'), ('page', 'clear_vars')]))
    PAGE('clear_vars', ON_ENTER([
        set_('tw_operation_state', '0'), set_('tw_text1', ''), set_('tw_text2', ''), set_('tw_text3', ''), set_('tw_text4', ''),
        set_('tw_action_text1', ''), set_('tw_action_text2', ''), set_('tw_action_param', ''), set_('tw_has_action2', '0'),
        set_('tw_action2', ''), set_('tw_action2_param', ''), set_('tw_has_cancel', '0'), set_('tw_cancel_action', ''),
        set_('tw_cancel_param', ''), set_('kb_hint', ''), ('page', '%tw_clear_destination%')]))

    M = '-' * 0
    main_items = [
        item(tr('kb_install', 'Install zip', 'Instalar zip'), goto('install_pick', ('mount', '/external_sd'), set_('kb_path', '/external_sd'), set_('tw_selectimage', '0'))),
        item(tr('kb_backup', 'Backup', 'Copia de seguridad'), goto('backup_setup', set_('tw_backup_list', '/boot;/system;/data;'), ('mount', '/external_sd'))),
        item(tr('kb_restore', 'Restore', 'Restaurar'), goto('restore_storage')),
        item(tr('kb_wipe', 'Wipe / Format', 'Borrar / Formatear'), goto('wipe')),
        item(tr('kb_mount', 'Mount / Unmount', 'Montar / Desmontar'), goto('mount')),
        item(tr('kb_files', 'File browser', 'Explorador de archivos'), goto('files', ('mount', '/external_sd'), set_('kb_path', '/external_sd'))),
        item(tr('kb_logs', 'Logs', 'Registros'), goto('logs')),
        item(tr('kb_reboot', 'Reboot / Power off', 'Reiniciar / Apagar'), goto('reboot')),
        item(tr('kb_tools', 'ADB, settings, extras', 'ADB, ajustes, extras'), goto('tools')),
    ]
    PAGE('main2', chrome([(tr('kb_title_main', 'KYF37 Recovery', 'Recuperacion KYF37'), None, None)],
                         tr('kb_ver', 'TWRP %tw_version%  keitai UI', 'TWRP %tw_version%  interfaz keitai')),
         KEY('59', [set_('kb_hint', '')]), KEY('254', ['screenshot']),
         KEYMENU(main_items))

    # --- generic confirmation (two step) ------------------------------------
    confirm1_items = [
        item(tr('kb_cancel_safe', 'Cancel (safe)', 'Cancelar (seguro)'), [('page', '%kb_c_back%')]),
        item(tr('kb_continue', 'Continue...', 'Continuar...'), [set_('kb_hint', ''), ('page', 'confirm2')], danger=True, cond=('kb_c_two', '=', '1')),
        item(tr('kb_yes_do', 'Yes, do it', 'Si, hacerlo'), [set_('tw_operation_state', '0'), ('page', 'action_page')], danger=True, cond=('kb_c_two', '=', '0')),
    ]
    PAGE('confirm1', chrome([(tr('kb_confirm', 'Please confirm', 'Confirme'), C['accent'], None)], None, 'nav'),
         TEXT(16, 120, '%kb_c_title%', 'font_l', C['text']),
         TEXT(16, 176, '%kb_c_l1%', 'font_m', C['muted']), TEXT(16, 214, '%kb_c_l2%', 'font_m', C['muted']),
         TEXT(16, 252, '%kb_c_l3%', 'font_m', C['muted']),
         TEXT(16, 310, tr('kb_c_default', 'The highlighted choice is the safe one.', 'La opcion marcada es la segura.'), 'font_s', C['ok']),
         nav_keys('%kb_c_back%'),
         KEYMENU(confirm1_items, y=360, h=300, keepfocus=False))

    confirm2_items = [
        item(tr('kb_cancel_safe', 'Cancel (safe)', 'Cancelar (seguro)'), [('page', '%kb_c_back%')]),
        item(tr('kb_c_confirm0', 'Press 0 to CONFIRM', 'Pulse 0 para CONFIRMAR'), [set_('tw_operation_state', '0'), ('page', 'action_page')],
             danger=True, hotkey=0, shortcutonly=True),
    ]
    PAGE('confirm2', chrome([(tr('kb_final', 'FINAL CHECK', 'COMPROBACION FINAL'), C['danger'], None)], None, 'nav'),
         TEXT(16, 120, '%kb_c_title%', 'font_l', C['danger']),
         TEXT(16, 176, tr('kb_c_irrev', 'This cannot be undone.', 'No se puede deshacer.'), 'font_m', C['text']),
         TEXT(16, 214, '%kb_c_l1%', 'font_m', C['muted']), TEXT(16, 252, '%kb_c_l2%', 'font_m', C['muted']),
         TEXT(16, 290, tr('kb_c_zero', 'To go ahead press the key 0.', 'Para continuar pulse la tecla 0.'), 'font_m', C['accent']),
         TEXT(16, 328, tr('kb_c_okno', 'OK alone does NOT confirm.', 'OK solo NO confirma.'), 'font_s', C['ok']),
         TEXT(16, 620, '%kb_hint%', 'font_m', C['danger']),
         nav_keys('%kb_c_back%'),
         KEYMENU(confirm2_items, y=380, h=220, keepfocus=False))

    # --- operation runner ---------------------------------------------------
    run_hooks = (
        '<action><condition var1="tw_operation_state" var2="1"/>' + action_xml([('page', 'action_complete')]) + '</action>'
        '<action><condition var1="tw_has_action2" var2="0"/>' + action_xml([('%tw_action%', '%tw_action_param%')]) + '</action>'
        '<action><condition var1="tw_has_action2" var2="1"/>' + action_xml([('%tw_action%', '%tw_action_param%'), ('%tw_action2%', '%tw_action2_param%')]) + '</action>')
    PAGE('action_page', chrome([('%tw_action_text1%', None, None)], '%tw_action_text2%', 'busy'),
         CONSOLE(110, 560), PROGRESS(690),
         TEXT(16, 730, '%tw_file_progress%  %tw_size_progress%', 'font_s', C['muted']),
         KEY('back', [('%tw_cancel_action%', '%tw_cancel_param%')], cond=('tw_has_cancel', '=', '1')),
         run_hooks)
    PAGE('singleaction_page', chrome([('%tw_action_text1%', None, None)], '%tw_action_text2%', 'busy'),
         CONSOLE(110, 560), PROGRESS(690),
         '<action><condition var1="tw_operation_state" var2="1"/>' + action_xml([set_('tw_page_done', '1')]) + '</action>'
         '<action><condition var1="tw_has_action2" var2="0"/>' + action_xml([('%tw_action%', '%tw_action_param%')]) + '</action>'
         '<action><condition var1="tw_has_action2" var2="1"/>' + action_xml([('%tw_action%', '%tw_action_param%'), ('%tw_action2%', '%tw_action2_param%')]) + '</action>')

    done_items = [
        item(tr('kb_back_menu', 'Back', 'Volver'), [set_('tw_clear_destination', '%kb_c_back%'), ('page', 'clear_vars')]),
        item(tr('kb_main_menu', 'Main menu', 'Menu principal'), [set_('tw_clear_destination', 'main2'), ('page', 'clear_vars')]),
        item(tr('kb_reboot_sys', 'Reboot system', 'Reiniciar sistema'), [('reboot', 'system')]),
    ]
    PAGE('action_complete',
         chrome([('%tw_complete_text1%', None, None)], None, 'nav'),
         TEXT(16, 74, tr('kb_ok', 'Successful', 'Correcto'), 'font_s', C['ok'], 0, ('tw_operation_status', '=', '0')),
         TEXT(16, 74, tr('kb_failed', 'FAILED - see log below', 'FALLO - vea el registro'), 'font_s', C['danger'], 0, ('tw_operation_status', '!=', '0')),
         CONSOLE(110, 460),
         KEY('back', [set_('tw_clear_destination', '%kb_c_back%'), ('page', 'clear_vars')]),
         KEY('60', [set_('tw_clear_destination', '%kb_c_back%'), ('page', 'clear_vars')]),
         KEY('59', [set_('tw_clear_destination', 'main2'), ('page', 'clear_vars')]),
         KEYMENU(done_items, y=598, h=180, keepfocus=False, paging=False))

    # --- install ------------------------------------------------------------
    PAGE('install_pick',
         chrome([(tr('kb_install', 'Install zip', 'Instalar zip'), None, None)],
                tr('kb_pick_zip', 'Pick a .zip  (Clear = up / back)', 'Elija un .zip  (Clear = subir / volver)')),
         TEXT(16, 104, '%kb_path%', 'font_s', C['accent']),
         nav_keys('main2'),
         KEYMENU([], y=134, h=644, numbered=False, keepfocus=True,
                 browse=BROWSE('/external_sd', '/external_sd', '.zip;.ozip', [('queuezip', ''), ('page', 'install_confirm')], showsize=False)))
    inst_items = [
        item(tr('kb_cancel_safe', 'Cancel (safe)', 'Cancelar (seguro)'), [('queueclear', ''), ('page', 'install_pick')]),
        item(tr('kb_install_now', 'Install this zip', 'Instalar este zip'), [set_('tw_operation_state', '0'), set_('kb_c_back', 'install_pick'), ('flash', 'flash_zip')], danger=True),
        item(tr('kb_verify', 'Verify zip signature', 'Verificar firma del zip'), var='tw_signed_zip_verify'),
    ]
    PAGE('install_confirm', chrome([(tr('kb_install_q', 'Install this zip?', 'Instalar este zip?'), C['accent'], None)], None, 'nav'),
         TEXT(16, 120, '%tw_file%', 'font_m', C['text']),
         TEXT(16, 160, '%kb_path%', 'font_s', C['muted']),
         TEXT(16, 200, tr('kb_zip_warn', 'Installing runs the zip script as root.', 'Instalar ejecuta el script del zip como root.'), 'font_s', C['muted']),
         TEXT(16, 232, tr('kb_zip_nowipe', 'Keep the USB cable and battery connected.', 'Mantenga cable USB y bateria.'), 'font_s', C['muted']),
         KEY('back', [('queueclear', ''), ('page', 'install_pick')]), KEY('60', [('queueclear', ''), ('page', 'install_pick')]),
         KEY('59', [('queueclear', ''), ('page', 'main')]), KEY('254', ['screenshot']),
         KEYMENU(inst_items, y=290, h=300, keepfocus=False))
    PAGE('flash_zip', chrome([(tr('kb_installing', 'Installing zip', 'Instalando zip'), None, None)],
                             tr('kb_zip_count', 'Zip %tw_zip_index% of %tw_zip_queue_count%: %tw_file%'), 'busy'),
         CONSOLE(110, 560), PROGRESS(690),
         '<action><condition var1="tw_operation_state" var2="1"/>' + action_xml([('page', 'flash_done')]) + '</action>')
    flash_done_items = [
        item(tr('kb_back_menu', 'Back', 'Volver'), [set_('tw_clear_destination', 'install_pick'), ('page', 'clear_vars')]),
        item(tr('kb_main_menu', 'Main menu', 'Menu principal'), [set_('tw_clear_destination', 'main2'), ('page', 'clear_vars')]),
        item(tr('kb_reboot_sys', 'Reboot system', 'Reiniciar sistema'), [('reboot', 'system')]),
        item(tr('kb_wipe_cd', 'Wipe cache + dalvik', 'Borrar cache + dalvik'), confirm('Wipe cache and dalvik?', ['Only caches are removed.'], 'wipe', '/cache', 'flash_done', False,
                                                                          'Cache and dalvik wipe complete', 'Wiping cache and dalvik...',
                                                                          extra=[set_('tw_has_action2', '1'), set_('tw_action2', 'wipe'), set_('tw_action2_param', 'dalvik')])),
    ]
    PAGE('flash_done',
         chrome([(tr('kb_inst_done', 'Install complete', 'Instalacion completa'), C['ok'], ('tw_operation_status', '=', '0')),
                 (tr('kb_inst_fail', 'Install FAILED', 'Instalacion FALLIDA'), C['danger'], ('tw_operation_status', '!=', '0'))],
                '%tw_file%', 'nav'),
         CONSOLE(110, 400),
         KEY('back', [set_('tw_clear_destination', 'install_pick'), ('page', 'clear_vars')]),
         KEY('60', [set_('tw_clear_destination', 'install_pick'), ('page', 'clear_vars')]),
         KEY('59', [set_('tw_clear_destination', 'main2'), ('page', 'clear_vars')]),
         KEYMENU(flash_done_items, y=540, h=238, keepfocus=False, paging=False))

    # --- backup ---------------------------------------------------------------
    start_backup = [set_('kb_hint', ''), ('checkpartitionlist', 'tw_backup_list'), set_('tw_enable_adb_backup', '0'), set_('tw_operation_state', '0'),
                    set_('kb_c_back', 'backup_setup'), ('page', 'backup_check')]
    bk_items = [
        item(tr('kb_bk_boot', 'Boot', 'Boot'), member='/boot', listvar='tw_backup_list'),
        item(tr('kb_bk_system', 'System', 'System'), member='/system', listvar='tw_backup_list'),
        item(tr('kb_bk_data', 'Data', 'Datos'), member='/data', listvar='tw_backup_list'),
        item(tr('kb_bk_sd', 'Save to: SD card (OK = internal)', 'Guardar en: SD (OK = interna)'),
             [('mount', '/data'), set_('tw_storage_path', '/data/media/0')], cond=('tw_storage_path', '=', '/external_sd')),
        item(tr('kb_bk_int', 'Save to: internal (OK = SD card)', 'Guardar en: interna (OK = SD)'),
             [('mount', '/external_sd'), set_('tw_storage_path', '/external_sd')], cond=('tw_storage_path', '!=', '/external_sd')),
        item(tr('kb_bk_start', 'Start backup', 'Iniciar copia'), start_backup, hotkey=9),
    ]
    PAGE('backup_setup', chrome([(tr('kb_backup', 'Backup', 'Copia de seguridad'), None, None)],
                                tr('kb_bk_info', 'To %tw_storage_path%   free %tw_storage_free_size% MB')),
         nav_keys('main2'), TEXT(16, 735, '%kb_hint%', 'font_m', C['danger']), KEYMENU(bk_items, h=630))
    PAGE('backup_check',
         '<action><condition var1="tw_check_partition_list" op="&gt;" var2="0"/>' + action_xml([('generatebackupname', ''), ('page', 'backup_run')]) + '</action>'
         '<action><condition var1="tw_check_partition_list" op="=" var2="0"/>' + action_xml([set_('kb_hint', 'Select at least one partition'), ('page', 'backup_setup')]) + '</action>')
    PAGE('backup_run', chrome([(tr('kb_bk_running', 'Backing up...', 'Copiando...'), None, None)], '%tw_operation% %tw_partition%', 'busy'),
         CONSOLE(110, 520), PROGRESS(650),
         TEXT(16, 690, '%tw_file_progress%', 'font_s', C['muted']), TEXT(16, 722, '%tw_size_progress%', 'font_s', C['muted']),
         KEY('back', ['cancelbackup']),
         '<action>' + action_xml([('nandroid', 'backup')]) + '</action>'
         '<action><condition var1="tw_operation_state" var2="1"/>' + action_xml([
             set_('kb_c_back', 'backup_setup'), set_('tw_complete_text1', 'Backup complete'), ('page', 'action_complete')]) + '</action>')

    # --- restore ---------------------------------------------------------------
    rs_items = [
        item(tr('kb_rs_sd', 'Backups on SD card', 'Copias en la tarjeta SD'),
             goto('restore_pick', ('mount', '/external_sd'), set_('tw_storage_path', '/external_sd'), set_('kb_root', 'tw_backups_folder'), set_('kb_path', 'tw_backups_folder'))),
        item(tr('kb_rs_int', 'Backups on internal storage', 'Copias en almacenamiento interno'),
             goto('restore_pick', ('mount', '/data'), set_('tw_storage_path', '/data/media/0'), set_('kb_root', 'tw_backups_folder'), set_('kb_path', 'tw_backups_folder'))),
    ]
    menu_page('restore_storage', tr('kb_restore', 'Restore', 'Restaurar'), rs_items, 'main2',
              tr('kb_rs_pick_src', 'Where are the backups?', 'Donde estan las copias?'))
    PAGE('restore_pick',
         chrome([(tr('kb_restore', 'Restore', 'Restaurar'), None, None)], tr('kb_rs_pick', 'Pick a backup (newest first)', 'Elija una copia (la mas nueva primero)')),
         TEXT(16, 104, '%kb_path%', 'font_s', C['accent']),
         nav_keys('restore_storage'),
         KEYMENU([], y=134, h=644, numbered=False,
                 browse=BROWSE('/external_sd', '/external_sd', '', [('readBackup', ''), ('page', 'restore_select')], filevar='tw_restore',
                               selvar='tw_restore_name', choosedirs=True, reverse=True, rootvar='kb_root')))
    rsel_items = [
        item(tr('kb_bk_boot', 'Boot', 'Boot'), member='/boot', listvar='tw_restore_selected', availvar='tw_restore_list'),
        item(tr('kb_bk_system', 'System', 'System'), member='/system', listvar='tw_restore_selected', availvar='tw_restore_list'),
        item(tr('kb_bk_data', 'Data', 'Datos'), member='/data', listvar='tw_restore_selected', availvar='tw_restore_list'),
        item(tr('kb_rs_start', 'Restore selected...', 'Restaurar seleccion...'),
             confirm('Restore this backup?', ['%tw_restore_name%', 'Overwrites the selected partitions.'], 'nandroid', 'restore', 'restore_select', True,
                     'Restore complete', 'Restoring...') , danger=True, hotkey=9),
        item(tr('kb_rs_del', 'Delete this backup...', 'Borrar esta copia...'),
             confirm('Delete this backup?', ['%tw_restore_name%', 'The backup folder is removed.'], 'cmd', 'rm -rf "%tw_restore%"', 'restore_pick', True,
                     'Backup deleted', 'Deleting backup...'), danger=True),
    ]
    PAGE('restore_select', chrome([(tr('kb_restore', 'Restore', 'Restaurar'), None, None)], '%tw_restore_name%'),
         nav_keys('restore_pick'), KEYMENU(rsel_items))

    # --- wipe -----------------------------------------------------------------
    wipe_items = [
        item(tr('kb_w_cache', 'Wipe cache + dalvik', 'Borrar cache + dalvik'),
             confirm('Wipe cache and dalvik?', ['Only caches are removed.'], 'wipe', '/cache', 'wipe', False, 'Cache and dalvik wipe complete', 'Wiping cache and dalvik...',
                     extra=[set_('tw_has_action2', '1'), set_('tw_action2', 'wipe'), set_('tw_action2_param', 'dalvik')])),
        item(tr('kb_w_factory', 'Factory reset (data+cache)', 'Restablecer (datos+cache)'),
             confirm('Factory reset?', ['Erases apps and settings in /data.', 'Internal storage files are kept.'], 'wipe', 'data', 'wipe', True, 'Factory reset complete', 'Factory reset...'), danger=True),
        item(tr('kb_w_format', 'Format data (ALL data)', 'Formatear datos (TODO)'),
             confirm('Format data?', ['Erases EVERYTHING in /data', 'including internal storage.'], 'wipe', 'DATAMEDIA', 'wipe', True, 'Format complete', 'Formatting data...'), danger=True),
        item(tr('kb_w_adv', 'Advanced wipe...', 'Borrado avanzado...'), goto('wipe_adv', set_('tw_wipe_list', ''))),
    ]
    menu_page('wipe', tr('kb_wipe', 'Wipe / Format', 'Borrar / Formatear'), wipe_items, 'main2',
              tr('kb_w_info', 'Every wipe asks twice. Default = Cancel.', 'Cada borrado pide doble confirmacion.'))
    adv_items = [
        item(tr('kb_wa_dalvik', 'Dalvik / ART cache', 'Cache dalvik / ART'), member='DALVIK', listvar='tw_wipe_list'),
        item(tr('kb_wa_cache', 'Cache', 'Cache'), member='/cache', listvar='tw_wipe_list'),
        item(tr('kb_bk_system', 'System', 'System'), member='/system', listvar='tw_wipe_list', ),
        item(tr('kb_bk_data', 'Data', 'Datos'), member='/data', listvar='tw_wipe_list'),
        item(tr('kb_wa_go', 'Wipe selected...', 'Borrar seleccion...'),
             [set_('kb_hint', ''), ('checkpartitionlist', 'tw_wipe_list'), set_('kb_c_back', 'wipe_adv'), ('page', 'wipe_adv_check')], danger=True, hotkey=9),
    ]
    PAGE('wipe_adv', chrome([(tr('kb_wa', 'Advanced wipe', 'Borrado avanzado'), None, None)],
                            tr('kb_wa_info', 'Tick what to wipe. Modem data is never offered.', 'Marque que borrar. Los datos del modem no se ofrecen.')),
         nav_keys('wipe'), TEXT(16, 735, '%kb_hint%', 'font_m', C['danger']), KEYMENU(adv_items, startfocus=0, h=630))
    wipe_go = confirm('Wipe selected partitions?', ['Selected: %tw_wipe_list%', 'Their contents are erased.'], 'wipe', 'LIST', 'wipe_adv', True,
                      'Wipe complete', 'Wiping...')
    PAGE('wipe_adv_check',
         '<action><condition var1="tw_check_partition_list" op="&gt;" var2="0"/>' + action_xml(wipe_go) + '</action>'
         '<action><condition var1="tw_check_partition_list" op="=" var2="0"/>' + action_xml([('page', 'wipe_adv_dalvik')]) + '</action>')
    # DALVIK-only selections do not count in checkpartitionlist; handle by allowing them when list not empty
    PAGE('wipe_adv_dalvik',
         '<action><condition var1="tw_wipe_list" op="=" var2=""/>' + action_xml([set_('kb_hint', 'Tick at least one item'), ('page', 'wipe_adv')]) + '</action>'
         '<action><condition var1="tw_wipe_list" op="!=" var2=""/>' + action_xml(wipe_go) + '</action>')

    # --- mount ----------------------------------------------------------------
    mount_items = [
        item(tr('kb_m_sd', 'SD card  /external_sd', 'Tarjeta SD  /external_sd'), mountpt='/external_sd'),
        item(tr('kb_m_data', 'Data  /data', 'Datos  /data'), mountpt='/data'),
        item(tr('kb_m_cache', 'Cache  /cache', 'Cache  /cache'), mountpt='/cache'),
        item(tr('kb_m_system', 'System  /system', 'System  /system'), mountpt='/system'),
    ]
    menu_page('mount', tr('kb_mount', 'Mount / Unmount', 'Montar / Desmontar'), mount_items, 'main2',
              tr('kb_m_info', 'OK toggles. [x] = mounted', 'OK alterna. [x] = montado'))

    # --- file browser ---------------------------------------------------------
    PAGE('files', chrome([(tr('kb_files', 'File browser', 'Explorador de archivos'), None, None)],
                         tr('kb_f_info', 'OK = open   Clear = up one folder', 'OK = abrir   Clear = subir carpeta')),
         TEXT(16, 104, '%kb_path%', 'font_s', C['accent']),
         nav_keys('main2'),
         KEYMENU([], y=134, h=644, numbered=False,
                 browse=BROWSE('/external_sd', '/', '', [('page', 'file_info')], filevar='tw_filename', selvar='tw_file')))
    fi_items = [
        item(tr('kb_fi_back', 'Back to list', 'Volver a la lista'), [('page', 'files')]),
        item(tr('kb_fi_view', 'View as text', 'Ver como texto'), [('page', 'text_view')]),
        item(tr('kb_fi_inst', 'Install as zip...', 'Instalar como zip...'), [('queuezip', ''), ('page', 'install_confirm')]),
        item(tr('kb_fi_del', 'Delete file...', 'Borrar archivo...'),
             confirm('Delete this file?', ['%tw_file%', 'It cannot be recovered.'], 'cmd', 'rm -f "%tw_filename%"', 'files', True, 'File deleted', 'Deleting...'), danger=True),
    ]
    PAGE('file_info', chrome([(tr('kb_fi', 'File', 'Archivo'), None, None)], None),
         TEXT(16, 110, '%tw_file%', 'font_m', C['text']), TEXT(16, 150, '%kb_path%', 'font_s', C['muted']),
         nav_keys('files'), KEYMENU(fi_items, y=200, h=500, keepfocus=False))
    PAGE('text_view', chrome([(tr('kb_view', 'Text viewer', 'Visor de texto'), None, None)], '%tw_file%', 'view'),
         nav_keys('file_info'),
         KEYMENU([], y=104, h=674, numbered=False, style='keymenu_log', textfile='<textfile pathvar="tw_filename" tail="600" wrap="40" start="top"/>'))

    # --- logs -------------------------------------------------------------------
    log_items = [
        item(tr('kb_l_twrp', 'Recovery log', 'Registro de recovery'), goto('log_view')),
        item(tr('kb_l_kmsg', 'Kernel log (dmesg)', 'Registro del kernel (dmesg)'), goto('kmsg_view', ('cmd', 'dmesg > /tmp/kmsg.txt'))),
        item(tr('kb_l_last', 'Last kernel log (before reboot)', 'Ultimo log del kernel (antes de reiniciar)'),
             goto('lastk_view', ('cmd', 'cat /proc/last_kmsg > /tmp/last_kmsg.txt 2>&1'))),
        item(tr('kb_l_copy', 'Copy logs to SD card', 'Copiar registros a la SD'),
             goto('action_page', ('mount', '/external_sd'), set_('tw_action', 'copylog'), set_('tw_action_param', ''), set_('tw_has_action2', '0'), set_('tw_action_text1', 'Copying logs...'),
                  set_('tw_complete_text1', 'Logs copied'), set_('kb_c_back', 'logs'), set_('tw_operation_state', '0'))),
    ]
    menu_page('logs', tr('kb_logs', 'Logs', 'Registros'), log_items, 'main2')
    for nm, ttl, path, back in (('log_view', 'Recovery log', '/tmp/recovery.log', 'logs'), ('kmsg_view', 'Kernel log', '/tmp/kmsg.txt', 'logs'),
                                ('lastk_view', 'Last kernel log', '/tmp/last_kmsg.txt', 'logs')):
        PAGE(nm, chrome([(ttl, None, None)], path, 'view'), nav_keys(back),
             KEYMENU([], y=104, h=674, numbered=False, style='keymenu_log', textfile='<textfile path="%s" tail="800" wrap="40" start="end"/>' % path))

    # --- reboot -----------------------------------------------------------------
    rb_items = [
        item(tr('kb_rb_sys', 'Reboot system', 'Reiniciar sistema'), [('reboot', 'system')]),
        item(tr('kb_rb_rec', 'Reboot recovery', 'Reiniciar recovery'), [('reboot', 'recovery')]),
        item(tr('kb_rb_off', 'Power off', 'Apagar'), [('reboot', 'poweroff')]),
    ]
    menu_page('reboot', tr('kb_reboot', 'Reboot / Power off', 'Reiniciar / Apagar'), rb_items, 'main2',
              tr('kb_rb_info', 'Reboot system clears the recovery flag.', 'Reiniciar sistema borra la marca de recovery.'))

    # --- tools ------------------------------------------------------------------
    tools_items = [
        item(tr('kb_t_sideload', 'ADB sideload', 'ADB sideload'),
             goto('action_page', set_('tw_action', 'adbsideload'), set_('tw_action_param', ''), set_('tw_has_action2', '0'),
                  set_('tw_action_text1', 'ADB sideload'), set_('tw_action_text2', 'adb sideload file.zip   (Back = cancel)'),
                  set_('tw_complete_text1', 'Sideload complete'), set_('tw_has_cancel', '1'), set_('tw_cancel_action', 'adbsideloadcancel'),
                  set_('tw_cancel_param', ''), set_('kb_c_back', 'tools'), set_('tw_operation_state', '0'))),
        item(tr('kb_t_settings', 'Settings', 'Ajustes'), goto('settings')),
        item(tr('kb_t_extras', 'Extras (scripts from SD)', 'Extras (scripts de la SD)'), goto('extras')),
        item(tr('kb_t_keys', 'Key help / about', 'Ayuda de teclas / acerca de'), goto('keyhelp')),
    ]
    menu_page('tools', tr('kb_t_title', 'Tools', 'Herramientas'), tools_items, 'main2',
              tr('kb_t_info', 'adb shell/push/pull/twrp work any time.', 'adb shell/push/pull/twrp funcionan siempre.'))
    set_items = [
        item(tr('kb_s_verify', 'Verify zip signature', 'Verificar firma de zips'), var='tw_signed_zip_verify'),
        item(tr('kb_s_digest', 'Skip zip digest check', 'Omitir comprobacion de digest'), var='tw_skip_digest_check_zip'),
        item(tr('kb_s_rmrf', 'Use rm -rf instead of formatting', 'Usar rm -rf en vez de formatear'), var='tw_rm_rf'),
        item(tr('kb_s_sha2', 'Skip digest generate on backup', 'No generar digest en copias'), var='tw_skip_digest_generate'),
        item(tr('kb_s_lang_en', 'Language: English', 'Idioma: English'), [set_('tw_language', 'en.xml'), 'setlanguage', 'reload']),
        item(tr('kb_s_lang_es', 'Idioma: Espanol', 'Idioma: Espanol'), [set_('tw_language', 'es.xml'), 'setlanguage', 'reload']),
    ]
    menu_page('settings', tr('kb_t_settings', 'Settings', 'Ajustes'), set_items, 'tools')
    key_text = [
        tr('kb_k1', 'Up/Down  move the highlight', 'Arriba/Abajo  mover la seleccion'),
        tr('kb_k2', 'OK  select    1-9,0  jump/select', 'OK  elegir    1-9,0  saltar/elegir'),
        tr('kb_k3', 'Clear or F2  back    F1 or End  main menu', 'Clear o F2  atras    F1 o Fin  menu principal'),
        tr('kb_k4', 'Left/Right  page    *  top    #  end', 'Izq/Der  pagina    *  inicio    #  final'),
        tr('kb_k5', 'Side key  screenshot to SD', 'Tecla lateral  captura a SD'),
        tr('kb_k6', 'Wipes ask twice: OK, then key 0.', 'Los borrados piden dos pasos: OK y tecla 0.'),
        tr('kb_k7', 'TWRP engine, keitai UI (KYF37)', 'Motor TWRP, interfaz keitai (KYF37)'),
    ]
    PAGE('keyhelp', chrome([(tr('kb_t_keys', 'Key help / about', 'Ayuda de teclas / acerca de'), None, None)], None), nav_keys('tools'),
         ''.join(TEXT(16, 110 + i * 46, t, 'font_m', C['text'] if i < 6 else C['muted']) for i, t in enumerate(key_text)))

    # --- extras: documented extension point --------------------------------------
    ex_items = [item(label, acts, danger=dng) for (label, acts, dng) in EXTRAS]
    ex_items.append(item(tr('kb_ex_run', 'Run a script from SD card...', 'Ejecutar un script de la SD...'),
                         goto('extras_pick', ('mount', '/external_sd'), set_('kb_path', '/external_sd/keitai-extras'))))
    menu_page('extras', tr('kb_t_extras', 'Extras (scripts from SD)', 'Extras (scripts de la SD)'), ex_items, 'tools',
              tr('kb_ex_info', 'Add your own rows: see RECOVERY-KEITAI.md', 'Anada sus filas: vea RECOVERY-KEITAI.md'))
    PAGE('extras_pick', chrome([(tr('kb_ex_run2', 'Run script', 'Ejecutar script'), None, None)], tr('kb_ex_dir', 'Scripts: /external_sd/keitai-extras/*.sh')),
         TEXT(16, 104, '%kb_path%', 'font_s', C['accent']), nav_keys('extras'),
         KEYMENU([], y=134, h=644, numbered=False,
                 browse=BROWSE('/external_sd/keitai-extras', '/external_sd/keitai-extras', '.sh', [
                     set_('kb_c_title', 'Run this script?'), set_('kb_c_l1', '%tw_file%'), set_('kb_c_l2', 'It runs as root in recovery.'), set_('kb_c_l3', ''),
                     set_('kb_c_back', 'extras_pick'), set_('kb_c_two', '1'), set_('tw_action', 'cmd'), set_('tw_action_param', 'sh "%tw_filename%"'),
                     set_('tw_has_action2', '0'), set_('tw_action_text1', 'Running script...'), set_('tw_complete_text1', 'Script finished'), set_('tw_has_cancel', '0'),
                     ('page', 'confirm1')])))

    # --- stubs needed by the TWRP core -------------------------------------------
    ro_items = [
        item(tr('kb_ro_keep', 'Keep system read-only (safe)', 'Mantener system de solo lectura (seguro)'), [('mountsystemtoggle', '1'), set_('tw_page_done', '1')]),
        item(tr('kb_ro_allow', 'Allow modifications', 'Permitir modificaciones'), [('mountsystemtoggle', '0'), set_('tw_page_done', '1')], danger=True),
    ]
    PAGE('system_readonly', chrome([(tr('kb_ro', 'System partition', 'Particion system'), C['accent'], None)], None, 'nav'),
         TEXT(16, 120, tr('kb_ro1', 'Keep the system partition unmodified?', 'Mantener system sin modificar?'), 'font_m', C['text']),
         TEXT(16, 160, tr('kb_ro2', 'Zips and adb can still change it.', 'Los zips y adb aun pueden cambiarla.'), 'font_s', C['muted']),
         '<action><touch key="back"/>' + action_xml([('mountsystemtoggle', '1'), set_('tw_page_done', '1')]) + '</action>',
         KEYMENU(ro_items, y=230, h=300, keepfocus=False))
    PAGE('decrypt', chrome([(tr('kb_enc', 'Encrypted data', 'Datos cifrados'), C['danger'], None)], None, 'nav'),
         TEXT(16, 120, tr('kb_enc1', 'Data is encrypted; this recovery cannot', 'Los datos estan cifrados; este recovery no'), 'font_m', C['text']),
         TEXT(16, 160, tr('kb_enc2', 'unlock it. Backup/restore of data is limited.', 'puede abrirlos. Copia de datos limitada.'), 'font_m', C['text']),
         '<action><touch key="back"/>' + action_xml([set_('tw_page_done', '1')]) + '</action>',
         KEYMENU([item(tr('kb_continue2', 'Continue', 'Continuar'), [set_('tw_page_done', '1')])], y=230, h=140))


EXTRAS = [
    # (label, actions, danger)  <- add rows here to extend the "Extras" menu, then re-run this script.
    # Example: ('Show uptime', [('cmd', 'uptime > /tmp/extras.txt'), ('page', 'extras_log')], False)
]

# ---------------------------------------------------------------- resources / styles


def head():
    fonts = [('font_t', 36), ('font_l', 34), ('font_m', 28), ('font_s', 22), ('font_hint', 26), ('font_row', 34), ('font_log', 22)]
    res = ''.join('<font name="%s" filename="RobotoCondensed-Regular.ttf" size="%d"/>' % f for f in fonts)
    res += '<font name="fixed" filename="DroidSansMono.ttf" size="19"/>'
    res += '<image name="progress_empty" filename="progress_empty"/><image name="progress_full" filename="progress_fill"/>'
    variables = ''.join('<variable name="%s" value="%s"/>' % kv for kv in [
        ('kb_path', '/external_sd'), ('kb_root', '/external_sd'), ('kb_hint', ''), ('kb_c_back', 'main2'), ('kb_c_two', '1'),
        ('kb_c_title', ''), ('kb_c_l1', ''), ('kb_c_l2', ''), ('kb_c_l3', ''), ('tw_selectimage', '0'),
        ('tw_hide_kb', '1'), ('tw_samsung_navbar', '0'), ('tw_gui_sort_order', '1')])
    styles = (
        '<style name="keymenu"><highlight color="%(accent)s"/><background color="%(bg)s"/>'
        '<font resource="font_row" color="%(text)s" highlightcolor="%(dark)s" spacing="26"/>'
        '<separator color="%(line)s" height="2"/>'
        '<fastscroll linecolor="%(line)s" rectcolor="%(accent)s" w="14" linew="2" rectw="8" recth="24"/></style>'
        '<style name="keymenu_log"><highlight color="%(line)s"/><background color="%(bg)s"/>'
        '<font resource="fixed" color="%(text)s" highlightcolor="%(accent)s" spacing="4"/>'
        '<separator color="%(bg)s" height="0"/>'
        '<fastscroll linecolor="%(line)s" rectcolor="%(accent)s" w="14" linew="2" rectw="8" recth="24"/></style>'
        '<style name="console"><fastscroll rectcolor="%(accent)s" w="14" rectw="8" recth="24"/>'
        '<color foreground="%(text)s" background="%(bg)s" scroll="%(bg)s"/><font resource="fixed"/></style>' % C)
    return ('<?xml version="1.0"?>\n<recovery><details><resolution width="%d" height="%d"/><author>KYF37</author>'
            '<title>Keitai</title><description>D-pad keitai theme (no cursor)</description><themeversion>{themeversion}</themeversion></details>'
            '<resources>%s</resources><variables>%s</variables><styles>%s</styles>' % (W, H, res, variables, styles))


def splash():
    return ('<?xml version="1.0"?>\n<recovery><details><resolution width="%d" height="%d"/><author>KYF37</author><title>splash</title>'
            '<description>splash</description><themeversion>{themeversion}</themeversion></details>'
            '<resources><font name="font_l" filename="RobotoCondensed-Regular.ttf" size="40"/></resources>'
            '<variables><variable name="x" value="0"/></variables>'
            '<pages><page name="splash"><background color="%s"/>%s%s</page></pages></recovery>'
            % (W, H, C['bg'], TEXT(240, 380, 'KYF37 Recovery', 'font_l', C['accent'], 5), TEXT(240, 440, 'TWRP engine  -  keitai UI', 'font_l', C['muted'], 5)))


def images():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('Pillow missing: skipping progress images (kept existing ones)')
        return
    d = OUT / 'images'
    d.mkdir(parents=True, exist_ok=True)
    for name, fill in (('progress_empty', None), ('progress_fill', C['accent'])):
        im = Image.new('RGBA', (460, 28), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 459, 27], fill=C['line'] if fill is None else fill)
        dr.rectangle([0, 0, 459, 27], outline=C['muted'] if fill is None else fill, width=2)
        im.save(d / (name + '.png'))


def en_file():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<language><display>English</display><resources>']
    for k, (en, es) in sorted(STRINGS.items()):
        lines.append('<string name="%s">%s</string>' % (k, en.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')))
    return '\n'.join(lines + ['</resources></language>']) + '\n'


def es_file():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<language><display>Espanol (keitai)</display><resources>']
    for k, (en, es) in sorted(STRINGS.items()):
        if es:
            lines.append('<string name="%s">%s</string>' % (k, esc(es).replace('&quot;', '"')))
    lines += ['</resources></language>']
    return '\n'.join(lines) + '\n'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_pages()
    ui = head() + '<pages>' + ''.join(pages) + '</pages></recovery>\n'
    (OUT / 'ui.xml').write_text(ui, encoding='utf-8', newline='\n')
    (OUT / 'splash.xml').write_text(splash(), encoding='utf-8', newline='\n')
    (HERE / 'es-strings.xml').write_text(es_file(), encoding='utf-8', newline='\n')
    (HERE / 'en-strings.xml').write_text(en_file(), encoding='utf-8', newline='\n')
    images()
    print('pages: %d  strings: %d  ui.xml: %d bytes' % (len(pages), len(STRINGS), len(ui)))


if __name__ == '__main__':
    main()
