package org.kyf37.contacts;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.ContactsContract;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Add / edit a contact. Up/Down move between fields, the text keyboard (TT9) types, Clear deletes a character
 * (the framework turns Clear into backspace while a field has text), F1 or the Save row stores the contact.
 */
public final class ContactEditActivity extends Activity {
    private KUi.Screen screen;
    private EditText fName, fMobile, fHome, fWork, fEmail, fNote;
    private long contactId = -1;
    private Store.Card original = new Store.Card();
    private boolean saved;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_PAN);
        screen = KUi.screen(this, "New contact");
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        sv.setVerticalScrollBarEnabled(false);
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(KUi.px(this, 12), KUi.px(this, 6), KUi.px(this, 12), KUi.px(this, 12));
        fName = field(col, "Name", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_WORDS);
        fMobile = field(col, "Mobile", InputType.TYPE_CLASS_PHONE);
        fHome = field(col, "Home phone", InputType.TYPE_CLASS_PHONE);
        fWork = field(col, "Work phone", InputType.TYPE_CLASS_PHONE);
        fEmail = field(col, "E-mail", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        fNote = field(col, "Note", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        TextView save = new TextView(this);
        save.setText("Save");
        save.setTextSize(20);
        save.setTypeface(Typeface.DEFAULT_BOLD);
        save.setTextColor(Color.WHITE);
        save.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setColor(KUi.headerColor(this));
        g.setCornerRadius(KUi.px(this, 8));
        save.setBackground(g);
        save.setFocusable(true);
        save.setClickable(true);
        save.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { save(); } });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, KUi.px(this, 48));
        lp.topMargin = KUi.px(this, 14);
        col.addView(save, lp);
        sv.addView(col);
        screen.body.addView(sv);
        screen.hints("F1 Save", "Up/Down  Field", "Clear  Delete");

        Intent in = getIntent();
        if (Intent.ACTION_EDIT.equals(in.getAction()) && in.getData() != null) {
            contactId = Store.contactId(this, in.getData());
            if (contactId < 0) { KUi.toast(this, "Contact not found"); finish(); return; }
            try { original = Store.read(this, contactId); }
            catch (RuntimeException e) { KUi.toast(this, "Contacts are not available"); finish(); return; }
            screen.setTitle("Edit contact");
        }
        if (b == null) fill(original);
        prefillFromExtras(in);
        fName.requestFocus();
    }

    private void fill(Store.Card k) {
        fName.setText(k.name); fMobile.setText(k.mobile); fHome.setText(k.home); fWork.setText(k.work);
        fEmail.setText(k.email); fNote.setText(k.note);
    }

    private void prefillFromExtras(Intent in) {
        Bundle x = in.getExtras();
        if (x == null) return;
        String name = x.getString(ContactsContract.Intents.Insert.NAME);
        String phone = x.getString(ContactsContract.Intents.Insert.PHONE);
        String email = x.getString(ContactsContract.Intents.Insert.EMAIL);
        String notes = x.getString(ContactsContract.Intents.Insert.NOTES);
        if (name != null && fName.getText().length() == 0) fName.setText(name);
        if (phone != null) {
            if (fMobile.getText().length() == 0) fMobile.setText(phone);
            else if (fHome.getText().length() == 0) fHome.setText(phone);
            else if (fWork.getText().length() == 0) fWork.setText(phone);
        }
        if (email != null && fEmail.getText().length() == 0) fEmail.setText(email);
        if (notes != null && fNote.getText().length() == 0) fNote.setText(notes);
    }

    private EditText field(LinearLayout col, String label, int inputType) {
        TextView l = new TextView(this);
        l.setText(label);
        l.setTextSize(13);
        l.setTextColor(KUi.accent(this));
        LinearLayout.LayoutParams llp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        llp.topMargin = KUi.px(this, 8);
        col.addView(l, llp);
        EditText e = new EditText(this);
        e.setSingleLine(true);
        e.setInputType(inputType);
        e.setTextSize(19);
        e.setTextColor(Color.WHITE);
        e.setHintTextColor(0xFF5B6773);
        e.setHint(label);
        GradientDrawable g = new GradientDrawable();
        g.setColor(0xFF1B2430);
        g.setStroke(1, 0xFF3A4654);
        g.setCornerRadius(KUi.px(this, 6));
        e.setBackground(g);
        e.setPadding(KUi.px(this, 10), KUi.px(this, 8), KUi.px(this, 10), KUi.px(this, 8));
        col.addView(e, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return e;
    }

    private Store.Card current() {
        Store.Card k = new Store.Card();
        k.name = fName.getText().toString().trim();
        k.mobile = fMobile.getText().toString().trim();
        k.home = fHome.getText().toString().trim();
        k.work = fWork.getText().toString().trim();
        k.email = fEmail.getText().toString().trim();
        k.note = fNote.getText().toString().trim();
        k.org = original.org;
        k.otherPhones = original.otherPhones;
        return k;
    }

    private boolean changed() {
        Store.Card k = current();
        return !(k.name.equals(original.name) && k.mobile.equals(original.mobile) && k.home.equals(original.home)
                && k.work.equals(original.work) && k.email.equals(original.email) && k.note.equals(original.note));
    }

    private void save() {
        Store.Card k = current();
        if (k.name.length() == 0 && k.mobile.length() == 0 && k.home.length() == 0 && k.work.length() == 0 && k.email.length() == 0) {
            KUi.toast(this, "Enter a name or a number");
            return;
        }
        if (k.name.length() == 0) k.name = k.mobile.length() > 0 ? k.mobile : (k.home.length() > 0 ? k.home : (k.work.length() > 0 ? k.work : k.email));
        try {
            long id = Store.save(this, contactId, k);
            saved = true;
            Intent r = new Intent();
            if (id >= 0) r.setData(ContactsContract.Contacts.getLookupUri(getContentResolver(),
                    android.content.ContentUris.withAppendedId(ContactsContract.Contacts.CONTENT_URI, id)));
            setResult(RESULT_OK, r);
            KUi.toast(this, "Saved");
            finish();
        } catch (Exception e) {
            KUi.toast(this, "Could not save the contact");
        }
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0 && KUi.isMenuKey(code)) { save(); return true; }
        return super.onKeyDown(code, ev);
    }

    @Override public void onBackPressed() {
        if (saved || !changed()) { super.onBackPressed(); return; }
        KUi.menu(this, "Leave without saving?", new String[] { "Save", "Discard changes", "Keep editing" }, new KUi.Pick() {
            @Override public void pick(int i) {
                if (i == 0) save();
                else if (i == 1) { saved = true; finish(); }
            }
        });
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }
}
