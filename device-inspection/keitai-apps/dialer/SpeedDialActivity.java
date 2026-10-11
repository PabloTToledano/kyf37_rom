package org.kyf37.dialer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.ContactsContract;
import android.telecom.TelecomManager;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;

/** Speed dial slots 1..9 (1 = voicemail). Hold the digit in the dialer to call a slot. */
public final class SpeedDialActivity extends Activity {
    private static final int REQ_PICK = 7;
    private KUi.Screen screen;
    private ListView list;
    private int pendingSlot;

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences("speed_dial", MODE_PRIVATE); }

    /** "number|name" for slots 2..9, null when empty. */
    static String slot(Context c, int n) { return prefs(c).getString("slot" + n, null); }

    private final KUi.Rows adapter = new KUi.Rows(this, false) {
        @Override public int getCount() { return 9; }
        @Override protected KUi.Row row(int pos) {
            KUi.Row r = new KUi.Row();
            r.num = String.valueOf(pos + 1);
            if (pos == 0) { r.title = "Voicemail"; r.sub = "Fixed"; return r; }
            String s = slot(SpeedDialActivity.this, pos + 1);
            if (s == null) { r.title = "(empty)"; r.titleColor = KUi.TEXT2; r.sub = "OK to assign a contact"; }
            else {
                String[] p = s.split("\\|", 2);
                r.title = p.length > 1 && p[1].length() > 0 ? p[1] : p[0];
                r.sub = p[0];
            }
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Speed dial");
        screen.hints("", "OK  Select", "Clear  Back");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { choose(pos); }
        });
        screen.body.addView(list);
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    private void choose(final int pos) {
        final int n = pos + 1;
        if (n == 1) { callVoicemail(); return; }
        final String s = slot(this, n);
        if (s == null) { assign(n); return; }
        KUi.menu(this, "Speed dial " + n, new String[] { "Call", "Change", "Remove" }, new KUi.Pick() {
            @Override public void pick(int i) {
                if (i == 0) {
                    try {
                        ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", s.split("\\|", 2)[0], null), new Bundle());
                    } catch (RuntimeException e) { KUi.toast(SpeedDialActivity.this, "Cannot place call"); }
                } else if (i == 1) assign(n);
                else { prefs(SpeedDialActivity.this).edit().remove("slot" + n).apply(); adapter.notifyDataSetChanged(); }
            }
        });
    }

    private void callVoicemail() {
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("voicemail", "", null), new Bundle());
        } catch (RuntimeException e) { KUi.toast(this, "Voicemail is not available"); }
    }

    private void assign(int n) {
        pendingSlot = n;
        try {
            startActivityForResult(new Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI), REQ_PICK);
        } catch (ActivityNotFoundException e) { KUi.toast(this, "No contacts app"); }
    }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        if (req != REQ_PICK || res != RESULT_OK || data == null || data.getData() == null) return;
        Cursor c = null;
        try {
            c = getContentResolver().query(data.getData(), new String[] {
                    ContactsContract.CommonDataKinds.Phone.NUMBER, ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME }, null, null, null);
            if (c != null && c.moveToFirst()) {
                prefs(this).edit().putString("slot" + pendingSlot, c.getString(0) + "|" + c.getString(1)).apply();
            }
        } catch (RuntimeException e) {
            KUi.toast(this, "Could not read the contact");
        } finally {
            if (c != null) c.close();
        }
        adapter.notifyDataSetChanged();
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        int d = KUi.digit(code);
        if (ev.getRepeatCount() == 0 && d >= 1) {
            list.setSelection(d - 1);
            choose(d - 1);
            return true;
        }
        return super.onKeyDown(code, ev);
    }
}
