package org.kyf37.dialer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.CallLog;
import android.provider.ContactsContract;
import android.telecom.TelecomManager;
import android.telephony.PhoneNumberUtils;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import java.util.ArrayList;

/**
 * Keypad dialer. Digits type, Call dials, Clear deletes a digit (empty: leaves), hold 0 = '+',
 * hold 1 = voicemail, hold 2..9 (empty number) = speed dial. Below the number: contacts matching what is typed,
 * or the recent calls when nothing is typed. Menu (F1) opens a numbered menu.
 */
public final class DialerActivity extends Activity {
    private KUi.Screen screen;
    private TextView numberView, nameView;
    private ListView list;
    private final StringBuilder number = new StringBuilder();
    private final ArrayList<String[]> items = new ArrayList<String[]>(); // {number, name, sub, right}
    private boolean listIsRecents = true;
    private boolean pickedFromList;
    private boolean longHandled;

    private final KUi.Rows adapter = new KUi.Rows(this, true) {
        @Override public int getCount() { return items.size(); }
        @Override protected KUi.Row row(int pos) {
            String[] it = items.get(pos);
            KUi.Row r = new KUi.Row();
            r.title = it[1] != null && it[1].length() > 0 ? it[1] : it[0];
            r.sub = it[1] != null && it[1].length() > 0 ? it[0] + (it[2].length() > 0 ? "  " + it[2] : "") : it[2];
            r.right = it[3];
            r.avatar = KUi.initial(it[1] != null && it[1].length() > 0 ? it[1] : "#");
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Phone");
        screen.hints("F1 Menu", "Call  Dial", "Clear  Back");
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        numberView = new TextView(this);
        numberView.setTextColor(Color.WHITE);
        numberView.setTextSize(36);
        numberView.setTypeface(Typeface.DEFAULT_BOLD);
        numberView.setGravity(Gravity.CENTER);
        numberView.setSingleLine(true);
        numberView.setEllipsize(android.text.TextUtils.TruncateAt.START);
        numberView.setPadding(KUi.px(this, 10), KUi.px(this, 8), KUi.px(this, 10), 0);
        col.addView(numberView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        nameView = new TextView(this);
        nameView.setTextColor(KUi.TEXT2);
        nameView.setTextSize(15);
        nameView.setGravity(Gravity.CENTER);
        nameView.setSingleLine(true);
        nameView.setPadding(KUi.px(this, 10), 0, KUi.px(this, 10), KUi.px(this, 6));
        col.addView(nameView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { dial(items.get(pos)[0]); }
        });
        list.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) { }
            @Override public void onNothingSelected(AdapterView<?> p) { }
        });
        col.addView(list, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        screen.body.addView(col);
        handleIntent(getIntent());
        refresh();
    }

    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        setIntent(i);
        number.setLength(0);
        handleIntent(i);
        refresh();
    }

    @Override protected void onResume() {
        super.onResume();
        KUi.forgetNames();
        refresh();
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    private void handleIntent(Intent i) {
        if (i == null) return;
        Uri d = i.getData();
        if (d != null && ("tel".equals(d.getScheme()) || "voicemail".equals(d.getScheme()))) {
            if ("voicemail".equals(d.getScheme())) { callVoicemail(); finish(); return; }
            String n = PhoneNumberUtils.getNumberFromIntent(i, this);
            if (n == null) n = d.getSchemeSpecificPart();
            if (n != null) number.append(Uri.decode(n));
        }
        String extra = i.getStringExtra("org.kyf37.dialer.NUMBER");
        if (extra != null) number.append(extra);
        // A call is already in progress and the user just pressed Call / opened the dialer: go back to it.
        if (number.length() == 0 && KeitaiInCallService.hasCalls() && !i.getBooleanExtra("org.kyf37.dialer.ADD_CALL", false)) {
            startActivity(new Intent(this, InCallActivity.class));
            finish();
        }
    }

    // ------------------------------------------------------------------------------------------- list contents

    private void refresh() {
        String n = number.toString();
        numberView.setText(n.length() == 0 ? "" : n);
        numberView.setHint("Enter number");
        numberView.setHintTextColor(0xFF5B6773);
        items.clear();
        pickedFromList = false;
        if (n.length() == 0) {
            listIsRecents = true;
            loadRecents();
            nameView.setText(items.isEmpty() ? "No recent calls" : "Recent calls");
        } else {
            listIsRecents = false;
            loadMatches(n);
            if (PhoneNumberUtils.isEmergencyNumber(n)) {
                nameView.setText("Emergency number");
                nameView.setTextColor(KUi.RED);
            } else {
                String nm = KUi.nameFor(this, n);
                nameView.setText(nm != null ? nm : (items.isEmpty() ? "" : items.size() + " matches"));
                nameView.setTextColor(KUi.TEXT2);
            }
        }
        if (n.length() == 0) nameView.setTextColor(KUi.TEXT2);
        adapter.notifyDataSetChanged();
        if (!items.isEmpty()) list.setSelection(0);
        screen.hints("F1 Menu", n.length() == 0 && items.isEmpty() ? "" : "Call  Dial", n.length() == 0 ? "Clear  Back" : "Clear  Delete");
    }

    private void loadRecents() {
        Cursor c = null;
        try {
            c = getContentResolver().query(CallLog.Calls.CONTENT_URI,
                    new String[] { CallLog.Calls.NUMBER, CallLog.Calls.CACHED_NAME, CallLog.Calls.DATE, CallLog.Calls.TYPE },
                    null, null, CallLog.Calls.DATE + " DESC LIMIT 60");
            java.util.HashSet<String> seen = new java.util.HashSet<String>();
            while (c != null && c.moveToNext() && items.size() < 8) {
                String num = c.getString(0);
                if (num == null || num.length() == 0 || !seen.add(num)) continue;
                String nm = c.getString(1);
                if (nm == null || nm.length() == 0) nm = KUi.nameFor(this, num);
                int type = c.getInt(3);
                String tag = type == CallLog.Calls.MISSED_TYPE ? "missed" : type == CallLog.Calls.OUTGOING_TYPE ? "dialed" : "received";
                items.add(new String[] { num, nm == null ? "" : nm, tag, KUi.when(this, c.getLong(2)) });
            }
        } catch (RuntimeException e) {
            // no permission / provider not ready: empty list
        } finally {
            if (c != null) c.close();
        }
    }

    private void loadMatches(String n) {
        Cursor c = null;
        try {
            Uri u = Uri.withAppendedPath(ContactsContract.CommonDataKinds.Phone.CONTENT_FILTER_URI, Uri.encode(n));
            c = getContentResolver().query(u, new String[] {
                    ContactsContract.CommonDataKinds.Phone.NUMBER, ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                    ContactsContract.CommonDataKinds.Phone.TYPE, ContactsContract.CommonDataKinds.Phone.LABEL },
                    null, null, ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " COLLATE LOCALIZED ASC");
            while (c != null && c.moveToNext() && items.size() < 12) {
                CharSequence label = ContactsContract.CommonDataKinds.Phone.getTypeLabel(getResources(), c.getInt(2), c.getString(3));
                items.add(new String[] { c.getString(0), c.getString(1), String.valueOf(label), "" });
            }
        } catch (RuntimeException e) {
            // ignore
        } finally {
            if (c != null) c.close();
        }
    }

    // ------------------------------------------------------------------------------------------- actions

    void dial(String n) {
        if (n == null || n.length() == 0) return;
        try {
            TelecomManager tm = (TelecomManager) getSystemService(TELECOM_SERVICE);
            tm.placeCall(Uri.fromParts("tel", n, null), new Bundle());
            // The in-call screen is opened by the InCallService; nothing else to do here.
            number.setLength(0);
            refresh();
        } catch (SecurityException e) {
            KUi.toast(this, "Calling is not permitted");
        } catch (RuntimeException e) {
            KUi.toast(this, "Cannot place call");
        }
    }

    private void callVoicemail() {
        try {
            TelecomManager tm = (TelecomManager) getSystemService(TELECOM_SERVICE);
            tm.placeCall(Uri.fromParts("voicemail", "", null), new Bundle());
        } catch (RuntimeException e) {
            KUi.toast(this, "Voicemail is not available");
        }
    }

    private void callPressed() {
        if (pickedFromList && list.getSelectedItemPosition() >= 0 && list.getSelectedItemPosition() < items.size()) {
            dial(items.get(list.getSelectedItemPosition())[0]);
            return;
        }
        if (number.length() > 0) { dial(number.toString()); return; }
        // Empty number: first press recalls the last dialed number, second press dials it.
        String last = CallLog.Calls.getLastOutgoingCall(this);
        if (last != null && last.length() > 0) {
            number.append(last);
            refresh();
        } else if (!items.isEmpty()) {
            dial(items.get(Math.max(0, list.getSelectedItemPosition()))[0]);
        }
    }

    private void menu() {
        final boolean has = number.length() > 0;
        final ArrayList<String> labels = new ArrayList<String>();
        final ArrayList<Integer> ids = new ArrayList<Integer>();
        add(labels, ids, "Recent calls", 1);
        add(labels, ids, "Contacts", 2);
        add(labels, ids, "Speed dial", 3);
        add(labels, ids, "Voicemail", 4);
        if (has) {
            add(labels, ids, "Save to contacts", 5);
            add(labels, ids, "Send message", 6);
            add(labels, ids, "Clear number", 7);
        }
        KUi.menu(this, "Phone menu", labels.toArray(new String[0]), new KUi.Pick() {
            @Override public void pick(int idx) {
                switch (ids.get(idx)) {
                    case 1: startActivity(new Intent(DialerActivity.this, RecentsActivity.class)); break;
                    case 2: startSafe(new Intent(Intent.ACTION_VIEW, ContactsContract.Contacts.CONTENT_URI)); break;
                    case 3: startActivity(new Intent(DialerActivity.this, SpeedDialActivity.class)); break;
                    case 4: callVoicemail(); break;
                    case 5: {
                        Intent i = new Intent(Intent.ACTION_INSERT_OR_EDIT);
                        i.setType(ContactsContract.Contacts.CONTENT_ITEM_TYPE);
                        i.putExtra(ContactsContract.Intents.Insert.PHONE, number.toString());
                        startSafe(i); break; }
                    case 6: startSafe(new Intent(Intent.ACTION_SENDTO, Uri.fromParts("smsto", number.toString(), null))); break;
                    case 7: number.setLength(0); refresh(); break;
                    default: break;
                }
            }
        });
    }

    private static void add(ArrayList<String> l, ArrayList<Integer> ids, String label, int id) { l.add(label); ids.add(id); }

    private void startSafe(Intent i) {
        try { startActivity(i); } catch (ActivityNotFoundException e) { KUi.toast(this, "Not available"); }
    }

    // ------------------------------------------------------------------------------------------- keys

    private static boolean dialKey(int code) {
        return (code >= KeyEvent.KEYCODE_0 && code <= KeyEvent.KEYCODE_9) || code == KeyEvent.KEYCODE_STAR || code == KeyEvent.KEYCODE_POUND
                || (code >= KeyEvent.KEYCODE_NUMPAD_0 && code <= KeyEvent.KEYCODE_NUMPAD_9);
    }

    private static String keyChar(int code) {
        if (code == KeyEvent.KEYCODE_STAR) return "*";
        if (code == KeyEvent.KEYCODE_POUND) return "#";
        return String.valueOf(KUi.digit(code));
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (dialKey(code)) {
            if (ev.getRepeatCount() == 0) { longHandled = false; ev.startTracking(); }
            return true;
        }
        if (ev.getRepeatCount() == 0) {
            if (code == KeyEvent.KEYCODE_CALL) { callPressed(); return true; }
            if (KUi.isMenuKey(code)) { menu(); return true; }
            if (code == KeyEvent.KEYCODE_DPAD_UP || code == KeyEvent.KEYCODE_DPAD_DOWN) pickedFromList = true;
        }
        return super.onKeyDown(code, ev);
    }

    @Override public boolean onKeyLongPress(int code, KeyEvent ev) {
        if (!dialKey(code)) return super.onKeyLongPress(code, ev);
        longHandled = true;
        if (code == KeyEvent.KEYCODE_0) {
            number.append('+');
            refresh();
            return true;
        }
        int d = KUi.digit(code);
        if (number.length() == 0 && d >= 1) {
            if (d == 1) { callVoicemail(); return true; }
            String sd = SpeedDialActivity.slot(this, d);
            if (sd != null) { dial(sd.split("\\|", 2)[0]); }
            else KUi.toast(this, "Speed dial " + d + " is empty");
            return true;
        }
        number.append(keyChar(code));
        refresh();
        return true;
    }

    @Override public boolean onKeyUp(int code, KeyEvent ev) {
        if (dialKey(code)) {
            if (!longHandled && !ev.isCanceled()) {
                number.append(keyChar(code));
                refresh();
            }
            longHandled = false;
            return true;
        }
        return super.onKeyUp(code, ev);
    }

    @Override public void onBackPressed() {
        if (number.length() > 0) {
            number.setLength(number.length() - 1);
            refresh();
        } else {
            finish();
        }
    }
}
