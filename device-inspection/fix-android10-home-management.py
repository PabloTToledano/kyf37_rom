from pathlib import Path
p=Path(__file__).with_name('Kyf37HomeRedesign.java.txt')
s=p.read_text(encoding='utf-8')
# Consume the release of a key that finished moving, so GridView cannot open it.
if '// Keypad launcher management v1' in s and 'moveKeyRelease' not in s:
    s=s.replace('    private boolean moving;', '    private int moveKeyRelease = -1;\n    private boolean moving;')
    s=s.replace('        int code = event.getKeyCode();\n        boolean moveKey', '        int code = event.getKeyCode();\n        if (code == moveKeyRelease && event.getAction() == KeyEvent.ACTION_UP) {\n            moveKeyRelease = -1;\n            return true;\n        }\n        boolean moveKey')
    s=s.replace('            if (event.getAction() == KeyEvent.ACTION_DOWN) onKeyDown(code, event);', '            if (event.getAction() == KeyEvent.ACTION_DOWN) {\n                if (moveKey) moveKeyRelease = code;\n                onKeyDown(code, event);\n            }')
    p.write_text(s,encoding='utf-8',newline='\n')
if '// Keypad launcher management v1' in s:
    print('launcher management already staged'); raise SystemExit
s=s.replace('    private boolean moving;', '    // Keypad launcher management v1\n    private final HashSet<String> hiddenApps = new HashSet<String>();\n    private TextView keyHints;\n    private boolean moving;')
s=s.replace('        setContentView(root);', '''        keyHints = new TextView(this);
        keyHints.setTextColor(Color.WHITE);
        keyHints.setTextSize(12);
        keyHints.setGravity(Gravity.CENTER);
        keyHints.setBackgroundColor(0xE6233C50);
        keyHints.setPadding(0, (int)(5*d), 0, (int)(5*d));
        root.addView(keyHints);
        setContentView(root);''')
s=s.replace('        discoverApps();\n        loadLayout();\n        int selected', '        moving = false;\n        movePos = -1;\n        discoverApps();\n        loadLayout();\n        int selected')
s=s.replace('        folders.clear();\n        android.content.SharedPreferences p = prefs();', '        folders.clear();\n        hiddenApps.clear();\n        hiddenApps.addAll(prefs().getStringSet("hidden_apps", Collections.<String>emptySet()));\n        android.content.SharedPreferences p = prefs();')
s=s.replace('prefs().edit().putString("layout2", o.toString()).apply();','prefs().edit().putString("layout2", o.toString()).putStringSet("hidden_apps", new HashSet<String>(hiddenApps)).apply();')
s=s.replace(' : apps.containsKey(k);',' : (apps.containsKey(k) && !hiddenApps.contains(k));')
s=s.replace('if (apps.containsKey(k) && placed.add(k))','if (apps.containsKey(k) && !hiddenApps.contains(k) && placed.add(k))')
s=s.replace('for (String k : appOrder) if (placed.add(k))','for (String k : appOrder) if (!hiddenApps.contains(k) && placed.add(k))')
s=s.replace('    private void updateBanner() {','''    private void updateBanner() {
        keyHints.setText(moving ? "D-pad: move   OK / Back: finish"
                : "OK: open   *: options   0 / #: page   Back: home");''')
s=s.replace('    // ------------------------------------------------------------------------------------------ keys', '''    // Handle move keys before GridView consumes navigation / OK.
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        int code = event.getKeyCode();
        boolean moveKey = moving && (code == KeyEvent.KEYCODE_DPAD_LEFT
                || code == KeyEvent.KEYCODE_DPAD_RIGHT || code == KeyEvent.KEYCODE_DPAD_UP
                || code == KeyEvent.KEYCODE_DPAD_DOWN || code == KeyEvent.KEYCODE_DPAD_CENTER
                || code == KeyEvent.KEYCODE_ENTER || code == KeyEvent.KEYCODE_BACK);
        if (moveKey || code == KeyEvent.KEYCODE_STAR || code == KeyEvent.KEYCODE_POUND
                || code == KeyEvent.KEYCODE_0) {
            if (event.getAction() == KeyEvent.ACTION_DOWN) onKeyDown(code, event);
            return true;
        }
        return super.dispatchKeyEvent(event);
    }

    // ------------------------------------------------------------------------------------------ keys''')
s=s.replace('            if (code == KeyEvent.KEYCODE_STAR)', '''            if (code == KeyEvent.KEYCODE_0 || code == KeyEvent.KEYCODE_POUND) {
                if (n > 0) {
                    int page = Math.max(COLS, (grid.getLastVisiblePosition() - grid.getFirstVisiblePosition() + 1) / COLS * COLS);
                    int target = Math.max(0, sel) + (code == KeyEvent.KEYCODE_POUND ? page : -page);
                    grid.setSelection(target >= n ? 0 : target < 0 ? n - 1 : target);
                }
                return true;
            }
            if (code == KeyEvent.KEYCODE_STAR)''')
s=s.replace('        choices.add("New folder");','''        if (tile != null && tile.folderId == null) {
            choices.add("Remove from launcher");
            choices.add("App info…");
        }
        choices.add("Restore hidden apps…");
        choices.add("Keypad help");
        choices.add("New folder");''')
s=s.replace('                if (action.equals("Move"))', '''                if (action.equals("Remove from launcher")) { hideApp(tile); return; }
                if (action.startsWith("App info")) {
                    launch(new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.parse("package:" + tile.intent.getComponent().getPackageName())));
                    return;
                }
                if (action.startsWith("Restore hidden")) { restoreApps(); return; }
                if (action.equals("Keypad help")) {
                    new android.app.AlertDialog.Builder(this).setTitle("Keypad help")
                        .setMessage("D-pad: select an app\\nOK: open\\n1–9: open numbered tiles\\n*: options / manage apps\\n0: previous page\\n#: next page\\nBack: leave folder / first tile\\nCall: Phone\\n\\nMove: D-pad rearranges; OK or Back saves.\\nRemoved apps stay installed. Restore them from * → Restore hidden apps.")
                        .setPositiveButton("OK", null).show();
                    return;
                }
                if (action.equals("Move"))''')
anchor='    private void pickFolder(final Tile app) {'
s=s.replace(anchor, '''    private void hideApp(final Tile app) {
        new android.app.AlertDialog.Builder(this).setTitle("Remove " + app.label + "?")
            .setMessage("Hide this app from the launcher. It stays installed and can be restored from Options.")
            .setNegativeButton(android.R.string.cancel, null)
            .setPositiveButton("Remove", (dialog, which) -> {
                int selected = grid.getSelectedItemPosition();
                hiddenApps.add(app.key);
                reconcile();
                showFolder(openFolder, selected);
            }).show();
    }

    private void restoreApps() {
        final ArrayList<String> keys = new ArrayList<String>();
        for (String key : appOrder) if (hiddenApps.contains(key)) keys.add(key);
        if (keys.isEmpty()) {
            Toast.makeText(this, "No hidden installed apps", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] labels = new String[keys.size() + 1];
        labels[0] = "Restore all";
        for (int i = 0; i < keys.size(); i++) labels[i + 1] = apps.get(keys.get(i)).label;
        new android.app.AlertDialog.Builder(this).setTitle("Restore to Home")
            .setItems(labels, (dialog, which) -> {
                if (which == 0) hiddenApps.clear();
                else hiddenApps.remove(keys.get(which - 1));
                reconcile();
                showFolder(openFolder, 0);
            }).setNegativeButton(android.R.string.cancel, null).show();
    }

'''+anchor)
p.write_text(s,encoding='utf-8',newline='\n')
print('launcher removal, restore, keypad management staged')
# Consume the release of a key that finished moving, so GridView cannot open it.
if '// Keypad launcher management v1' in s and 'moveKeyRelease' not in s:
    s=s.replace('    private boolean moving;', '    private int moveKeyRelease = -1;\n    private boolean moving;')
    s=s.replace('        int code = event.getKeyCode();\n        boolean moveKey', '        int code = event.getKeyCode();\n        if (code == moveKeyRelease && event.getAction() == KeyEvent.ACTION_UP) {\n            moveKeyRelease = -1;\n            return true;\n        }\n        boolean moveKey')
    s=s.replace('            if (event.getAction() == KeyEvent.ACTION_DOWN) onKeyDown(code, event);', '            if (event.getAction() == KeyEvent.ACTION_DOWN) {\n                if (moveKey) moveKeyRelease = code;\n                onKeyDown(code, event);\n            }')
    p.write_text(s,encoding='utf-8',newline='\n')

