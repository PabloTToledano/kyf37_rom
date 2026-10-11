package org.kyf37.contacts;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ContentUris;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.provider.ContactsContract;
import android.provider.ContactsContract.CommonDataKinds.Email;
import android.provider.ContactsContract.CommonDataKinds.Phone;
import android.telecom.TelecomManager;
import android.text.InputType;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.ListView;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;

/**
 * Contact list: sorted, letter jump with the digit keys (multitap: 2 = A B C ...), Left/Right = All / Favourites,
 * OK = open, Call = dial the primary number, F1 = menu (new, search, import/export vCard, delete).
 * Also serves PICK / GET_CONTENT / INSERT_OR_EDIT for other apps.
 */
public final class ContactListActivity extends Activity {
    private static final String[] LETTERS = { "0 ", "1", "ABC2", "DEF3", "GHI4", "JKL5", "MNO6", "PQRS7", "TUV8", "WXYZ9" };
    private static final int MODE_BROWSE = 0, MODE_PICK_CONTACT = 1, MODE_PICK_PHONE = 2, MODE_PICK_EMAIL = 3, MODE_INSERT_OR_EDIT = 4;

    private KUi.Screen screen;
    private ListView list;
    private int mode = MODE_BROWSE;
    private boolean favourites;
    private String filter = "";
    private final ArrayList<Store.C> rows = new ArrayList<Store.C>();
    private final Handler handler = new Handler();
    private int tapKey = -1, tapIndex;
    private long tapTime;
    private final Runnable clearBubble = new Runnable() { @Override public void run() { updateTitle(null); } };

    private final KUi.Rows adapter = new KUi.Rows(this, true) {
        @Override public int getCount() { return rows.size() + (mode == MODE_INSERT_OR_EDIT ? 1 : 0); }
        @Override protected KUi.Row row(int pos) {
            KUi.Row r = new KUi.Row();
            if (mode == MODE_INSERT_OR_EDIT) {
                if (pos == 0) { r.title = "Create new contact"; r.avatar = "+"; r.bold = true; return r; }
                pos--;
            }
            Store.C c = rows.get(pos);
            r.title = c.name;
            r.sub = c.number == null ? "" : c.number;
            r.right = c.starred ? "*" : "";
            r.rightColor = KUi.accent(ContactListActivity.this);
            r.avatar = KUi.initial(c.name);
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Contacts");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { open(pos); }
        });
        screen.body.addView(list);
        parseIntent(getIntent());
        updateTitle(null);
    }

    @Override protected void onResume() {
        super.onResume();
        KUi.forgetNames();
        reload();
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        setIntent(i);
        parseIntent(i);
        updateTitle(null);
        reload();
    }

    private void parseIntent(Intent i) {
        mode = MODE_BROWSE;
        String a = i.getAction();
        String type = i.getType();
        Uri d = i.getData();
        String ds = d == null ? "" : d.toString();
        if (Intent.ACTION_PICK.equals(a) || Intent.ACTION_GET_CONTENT.equals(a)) {
            if (Phone.CONTENT_TYPE.equals(type) || ds.startsWith(Phone.CONTENT_URI.toString()) || "vnd.android.cursor.dir/phone".equals(type) || ds.startsWith("content://contacts/phones")) mode = MODE_PICK_PHONE;
            else if (Email.CONTENT_TYPE.equals(type) || ds.startsWith(Email.CONTENT_URI.toString())) mode = MODE_PICK_EMAIL;
            else mode = MODE_PICK_CONTACT;
        } else if (Intent.ACTION_INSERT_OR_EDIT.equals(a)) {
            mode = MODE_INSERT_OR_EDIT;
        }
        String s = i.getStringExtra("org.kyf37.contacts.SEARCH");
        filter = s == null ? "" : s;
    }

    private void updateTitle(String bubble) {
        String t = mode == MODE_BROWSE ? (favourites ? "< Favourites >" : "< Contacts >") : (mode == MODE_INSERT_OR_EDIT ? "Add to contact" : "Choose contact");
        if (filter.length() > 0) t = "Find: " + filter;
        if (bubble != null) t = t + "   " + bubble;
        screen.setTitle(t);
        screen.hints(mode == MODE_BROWSE ? "F1 Menu" : "", "OK  Open", mode == MODE_BROWSE ? "Call  Dial" : "Clear  Back");
    }

    private void reload() {
        long keep = -1;
        int sel = list.getSelectedItemPosition();
        if (sel >= 0 && sel - (mode == MODE_INSERT_OR_EDIT ? 1 : 0) < rows.size() && sel - (mode == MODE_INSERT_OR_EDIT ? 1 : 0) >= 0)
            keep = rows.get(sel - (mode == MODE_INSERT_OR_EDIT ? 1 : 0)).id;
        rows.clear();
        try {
            rows.addAll(Store.load(this, filter, favourites));
        } catch (RuntimeException e) {
            KUi.toast(this, "Contacts are not available");
        }
        adapter.notifyDataSetChanged();
        int pos = 0;
        for (int i = 0; i < rows.size(); i++) if (rows.get(i).id == keep) { pos = i + (mode == MODE_INSERT_OR_EDIT ? 1 : 0); break; }
        if (adapter.getCount() > 0) list.setSelection(pos);
        updateTitle(null);
        if (rows.isEmpty() && mode != MODE_INSERT_OR_EDIT) screen.setTitle(filter.length() > 0 ? "No match" : (favourites ? "No favourites" : "No contacts"));
    }

    private Store.C at(int pos) {
        if (mode == MODE_INSERT_OR_EDIT) pos--;
        return pos >= 0 && pos < rows.size() ? rows.get(pos) : null;
    }

    // ------------------------------------------------------------------------------------------ opening

    private void open(int pos) {
        if (mode == MODE_INSERT_OR_EDIT && pos == 0) {
            Intent i = new Intent(Intent.ACTION_INSERT, ContactsContract.Contacts.CONTENT_URI).putExtras(getIntent().getExtras() == null ? new Bundle() : getIntent().getExtras());
            startActivity(i);
            finish();
            return;
        }
        final Store.C c = at(pos);
        if (c == null) return;
        switch (mode) {
            case MODE_PICK_CONTACT:
                setResult(RESULT_OK, new Intent().setData(c.uri()));
                finish();
                break;
            case MODE_PICK_PHONE: pickData(c, true); break;
            case MODE_PICK_EMAIL: pickData(c, false); break;
            case MODE_INSERT_OR_EDIT: {
                Intent i = new Intent(Intent.ACTION_EDIT, c.uri());
                if (getIntent().getExtras() != null) i.putExtras(getIntent().getExtras());
                startActivity(i);
                finish();
                break; }
            default: startActivity(new Intent(Intent.ACTION_VIEW, c.uri()).setClass(this, ContactViewActivity.class));
        }
    }

    private void pickData(Store.C c, boolean phone) {
        final ArrayList<Long> ids = new ArrayList<Long>();
        ArrayList<String> labels = new ArrayList<String>();
        for (Store.Datum d : Store.data(this, c.id)) {
            if (phone && Phone.CONTENT_ITEM_TYPE.equals(d.mime)) { ids.add(d.id); labels.add(String.valueOf(Phone.getTypeLabel(getResources(), d.type, d.label)) + "  " + d.v1); }
            if (!phone && Email.CONTENT_ITEM_TYPE.equals(d.mime)) { ids.add(d.id); labels.add(d.v1); }
        }
        final Uri base = phone ? Phone.CONTENT_URI : Email.CONTENT_URI;
        if (ids.isEmpty()) { KUi.toast(this, phone ? "No phone number" : "No e-mail address"); return; }
        if (ids.size() == 1) { done(base, ids.get(0)); return; }
        KUi.menu(this, c.name, labels.toArray(new String[0]), new KUi.Pick() {
            @Override public void pick(int i) { done(base, ids.get(i)); }
        });
    }

    private void done(Uri base, long dataId) {
        setResult(RESULT_OK, new Intent().setData(ContentUris.withAppendedId(base, dataId)));
        finish();
    }

    private void call(Store.C c) {
        if (c == null || c.number == null) { KUi.toast(this, "No phone number"); return; }
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", c.number, null), new Bundle());
        } catch (RuntimeException e) { KUi.toast(this, "Cannot place call"); }
    }

    // ------------------------------------------------------------------------------------------ menu

    private void menu() {
        String[] items = { "New contact", "Search", favourites ? "Show all contacts" : "Show favourites", "Delete selected", "Import vCard", "Export all (vCard)", "Export selected (vCard)" };
        KUi.menu(this, "Contacts menu", items, new KUi.Pick() {
            @Override public void pick(int i) {
                switch (i) {
                    case 0: startActivity(new Intent(Intent.ACTION_INSERT, ContactsContract.Contacts.CONTENT_URI).setClass(ContactListActivity.this, ContactEditActivity.class)); break;
                    case 1: search(); break;
                    case 2: favourites = !favourites; reload(); break;
                    case 3: deleteSelected(); break;
                    case 4: importVcf(); break;
                    case 5: exportAll(false); break;
                    case 6: exportAll(true); break;
                    default: break;
                }
            }
        });
    }

    private void search() {
        final EditText e = new EditText(this);
        e.setSingleLine(true);
        e.setText(filter);
        e.setInputType(InputType.TYPE_CLASS_TEXT);
        e.setSelection(e.length());
        final AlertDialog d = new AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                .setTitle("Search contacts").setView(e)
                .setPositiveButton("Search", (dlg, w) -> { filter = e.getText().toString().trim(); reload(); })
                .setNegativeButton("Cancel", null).create();
        d.show();
        e.requestFocus();
    }

    private void deleteSelected() {
        final Store.C c = at(list.getSelectedItemPosition());
        if (c == null) return;
        KUi.confirmTwice(this, "Delete " + c.name, "Delete", () -> {
            try { Store.delete(this, c.id); } catch (RuntimeException e) { KUi.toast(this, "Cannot delete"); }
            reload();
        });
    }

    private void importVcf() {
        final ArrayList<File> found = new ArrayList<File>();
        for (File root : VCard.roots(this)) {
            scan(root, found, 0);
            scan(new File(root, "Download"), found, 0);
            scan(new File(root, "Documents"), found, 0);
        }
        if (found.isEmpty()) { KUi.toast(this, "No .vcf files found on the SD card or phone storage"); return; }
        String[] names = new String[found.size()];
        for (int i = 0; i < names.length; i++) names[i] = found.get(i).getParentFile().getName() + "/" + found.get(i).getName();
        KUi.menu(this, "Import vCard", names, new KUi.Pick() {
            @Override public void pick(int i) { doImport(found.get(i)); }
        });
    }

    private static void scan(File dir, ArrayList<File> out, int depth) {
        File[] fs = dir.listFiles();
        if (fs == null) return;
        for (File f : fs) {
            if (f.isFile() && f.getName().toLowerCase().endsWith(".vcf") && !out.contains(f) && out.size() < 30) out.add(f);
        }
    }

    private void doImport(File f) {
        int ok = 0, bad = 0;
        try {
            for (Store.Card k : VCard.parse(f)) {
                try { Store.save(this, -1, k); ok++; } catch (Exception e) { bad++; }
            }
        } catch (Exception e) {
            KUi.toast(this, "Cannot read " + f.getName());
            return;
        }
        KUi.toast(this, "Imported " + ok + (bad > 0 ? ", failed " + bad : ""));
        reload();
    }

    private void exportAll(boolean onlySelected) {
        ArrayList<Store.Card> cards = new ArrayList<Store.Card>();
        try {
            if (onlySelected) {
                Store.C c = at(list.getSelectedItemPosition());
                if (c == null) return;
                cards.add(Store.read(this, c.id));
                cards.get(0).name = c.name;
            } else {
                for (Store.C c : Store.load(this, "", false)) {
                    Store.Card k = Store.read(this, c.id);
                    k.name = c.name;
                    cards.add(k);
                }
            }
        } catch (RuntimeException e) {
            KUi.toast(this, "Contacts are not available");
            return;
        }
        if (cards.isEmpty()) { KUi.toast(this, "Nothing to export"); return; }
        ArrayList<File> roots = VCard.roots(this);
        File dir = roots.isEmpty() ? new File("/sdcard") : roots.get(0);
        File out = new File(new File(dir, "Download"), "contacts-" + new java.text.SimpleDateFormat("yyyyMMdd-HHmm").format(new java.util.Date()) + ".vcf");
        try {
            out.getParentFile().mkdirs();
            FileOutputStream os = new FileOutputStream(out);
            try { os.write(VCard.write(cards).getBytes("UTF-8")); } finally { os.close(); }
            KUi.toast(this, "Saved " + cards.size() + " to " + out.getAbsolutePath());
        } catch (Exception e) {
            KUi.toast(this, "Cannot write " + out.getAbsolutePath());
        }
    }

    // ------------------------------------------------------------------------------------------ keys

    private void letterJump(int digit) {
        String letters = LETTERS[digit];
        long now = System.currentTimeMillis();
        if (digit == tapKey && now - tapTime < 1000) tapIndex = (tapIndex + 1) % letters.length();
        else tapIndex = 0;
        tapKey = digit;
        tapTime = now;
        char ch = letters.charAt(tapIndex);
        String target = String.valueOf(ch).toUpperCase();
        int found = -1;
        for (int i = 0; i < rows.size(); i++) {
            String n = rows.get(i).name == null ? "" : rows.get(i).name.toUpperCase();
            if (n.compareTo(target) >= 0) { found = i; break; }
        }
        if (found < 0 && !rows.isEmpty()) found = rows.size() - 1;
        if (found >= 0) list.setSelection(found + (mode == MODE_INSERT_OR_EDIT ? 1 : 0));
        updateTitle(target);
        handler.removeCallbacks(clearBubble);
        handler.postDelayed(clearBubble, 1200);
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0) {
            if (code == KeyEvent.KEYCODE_DPAD_LEFT || code == KeyEvent.KEYCODE_DPAD_RIGHT) {
                if (mode == MODE_BROWSE) { favourites = !favourites; reload(); }
                return true;
            }
            if (code == KeyEvent.KEYCODE_CALL && mode == MODE_BROWSE) { call(at(list.getSelectedItemPosition())); return true; }
            if (KUi.isMenuKey(code) && mode == MODE_BROWSE) { menu(); return true; }
            int d = KUi.digit(code);
            if (d >= 0) { letterJump(d); return true; }
        }
        return super.onKeyDown(code, ev);
    }

    @Override public void onBackPressed() {
        if (filter.length() > 0 && mode == MODE_BROWSE) { filter = ""; reload(); return; }
        if (mode != MODE_BROWSE) setResult(RESULT_CANCELED);
        super.onBackPressed();
    }
}
