package org.kyf37.contacts;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.ContactsContract;
import android.provider.ContactsContract.CommonDataKinds.Email;
import android.provider.ContactsContract.CommonDataKinds.Note;
import android.provider.ContactsContract.CommonDataKinds.Organization;
import android.provider.ContactsContract.CommonDataKinds.Phone;
import android.telecom.TelecomManager;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;

/**
 * One contact as numbered rows: Call / Message per phone number, e-mail, info rows, then Edit, Favourite, Share, Delete.
 * Digits jump to the row and activate it; OK activates the highlighted row; Call dials the first number.
 */
public final class ContactViewActivity extends Activity {
    private static final int CALL = 0, SMS = 1, MAIL = 2, INFO = 3, EDIT = 4, FAV = 5, EXPORT = 6, DELETE = 7;

    private static final class Item {
        int kind; String title; String sub; String value;
        Item(int k, String t, String s, String v) { kind = k; title = t; sub = s; value = v; }
    }

    private KUi.Screen screen;
    private ListView list;
    private long contactId = -1;
    private String name = "";
    private boolean starred;
    private final ArrayList<Item> items = new ArrayList<Item>();

    private final KUi.Rows adapter = new KUi.Rows(this, false) {
        @Override public int getCount() { return items.size(); }
        @Override protected KUi.Row row(int pos) {
            Item it = items.get(pos);
            KUi.Row r = new KUi.Row();
            r.num = pos < 9 ? String.valueOf(pos + 1) : (pos == 9 ? "0" : "");
            r.title = it.title;
            r.sub = it.sub;
            if (it.kind == DELETE) r.titleColor = KUi.RED;
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Contact");
        screen.hints("", "OK  Select", "Call  Dial");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { activate(pos); }
        });
        screen.body.addView(list);
        contactId = Store.contactId(this, getIntent().getData());
        if (contactId < 0) { KUi.toast(this, "Contact not found"); finish(); }
    }

    @Override protected void onResume() {
        super.onResume();
        if (contactId >= 0) build();
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    private void build() {
        items.clear();
        try {
            String n = Store.name(this, contactId);
            if (n == null) { finish(); return; } // deleted
            name = n;
            starred = Store.starred(this, contactId);
            screen.setTitle(name);
            for (Store.Datum d : Store.data(this, contactId)) {
                if (Phone.CONTENT_ITEM_TYPE.equals(d.mime) && d.v1 != null) {
                    String label = String.valueOf(Phone.getTypeLabel(getResources(), d.type, d.label));
                    items.add(new Item(CALL, "Call  " + d.v1, label, d.v1));
                    items.add(new Item(SMS, "Message  " + d.v1, label, d.v1));
                } else if (Email.CONTENT_ITEM_TYPE.equals(d.mime) && d.v1 != null) {
                    items.add(new Item(MAIL, "E-mail  " + d.v1, String.valueOf(Email.getTypeLabel(getResources(), d.type, d.label)), d.v1));
                } else if (Organization.CONTENT_ITEM_TYPE.equals(d.mime) && d.v1 != null) {
                    items.add(new Item(INFO, d.v1, "Organisation", null));
                } else if (Note.CONTENT_ITEM_TYPE.equals(d.mime) && d.v1 != null) {
                    items.add(new Item(INFO, d.v1, "Note", null));
                }
            }
        } catch (RuntimeException e) {
            KUi.toast(this, "Contacts are not available");
        }
        items.add(new Item(EDIT, "Edit contact", "", null));
        items.add(new Item(FAV, starred ? "Remove from favourites" : "Add to favourites", "", null));
        items.add(new Item(EXPORT, "Save as vCard file", "", null));
        items.add(new Item(DELETE, "Delete contact", "", null));
        adapter.notifyDataSetChanged();
        if (list.getSelectedItemPosition() < 0) list.setSelection(0);
    }

    private void activate(int pos) {
        if (pos < 0 || pos >= items.size()) return;
        Item it = items.get(pos);
        try {
            switch (it.kind) {
                case CALL: dial(it.value); break;
                case SMS:
                    startActivity(new Intent(Intent.ACTION_SENDTO, Uri.fromParts("smsto", it.value, null)));
                    break;
                case MAIL:
                    startActivity(new Intent(Intent.ACTION_SENDTO, Uri.fromParts("mailto", it.value, null)));
                    break;
                case EDIT:
                    startActivity(new Intent(Intent.ACTION_EDIT, ContactsContract.Contacts.getLookupUri(this.getContentResolver(),
                            android.content.ContentUris.withAppendedId(ContactsContract.Contacts.CONTENT_URI, contactId))).setClass(this, ContactEditActivity.class));
                    break;
                case FAV:
                    Store.setStarred(this, contactId, !starred);
                    build();
                    break;
                case EXPORT: export(); break;
                case DELETE:
                    KUi.confirmTwice(this, "Delete " + name, "Delete", new Runnable() {
                        @Override public void run() {
                            try { Store.delete(ContactViewActivity.this, contactId); } catch (RuntimeException e) { KUi.toast(ContactViewActivity.this, "Cannot delete"); return; }
                            finish();
                        }
                    });
                    break;
                default: break;
            }
        } catch (ActivityNotFoundException e) {
            KUi.toast(this, it.kind == MAIL ? "No e-mail app installed" : "Not available");
        } catch (RuntimeException e) {
            KUi.toast(this, "Not available");
        }
    }

    private void dial(String number) {
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", number, null), new Bundle());
        } catch (RuntimeException e) {
            KUi.toast(this, "Cannot place call");
        }
    }

    private void export() {
        try {
            Store.Card k = Store.read(this, contactId);
            k.name = name;
            ArrayList<Store.Card> one = new ArrayList<Store.Card>();
            one.add(k);
            ArrayList<File> roots = VCard.roots(this);
            File dir = roots.isEmpty() ? new File("/sdcard") : roots.get(0);
            File out = new File(new File(dir, "Download"), name.replaceAll("[^A-Za-z0-9_-]", "_") + ".vcf");
            out.getParentFile().mkdirs();
            FileOutputStream os = new FileOutputStream(out);
            try { os.write(VCard.write(one).getBytes("UTF-8")); } finally { os.close(); }
            KUi.toast(this, "Saved " + out.getAbsolutePath());
        } catch (Exception e) {
            KUi.toast(this, "Cannot save the file");
        }
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0) {
            int d = KUi.digit(code);
            if (d >= 0) {
                int row = d == 0 ? 9 : d - 1;
                if (row < items.size()) { list.setSelection(row); activate(row); }
                return true;
            }
            if (code == KeyEvent.KEYCODE_CALL) {
                int sel = list.getSelectedItemPosition();
                if (sel >= 0 && sel < items.size() && (items.get(sel).kind == CALL || items.get(sel).kind == SMS)) { dial(items.get(sel).value); return true; }
                for (int i = 0; i < items.size(); i++) if (items.get(i).kind == CALL) { activate(i); return true; }
                KUi.toast(this, "No phone number");
                return true;
            }
        }
        return super.onKeyDown(code, ev);
    }
}
