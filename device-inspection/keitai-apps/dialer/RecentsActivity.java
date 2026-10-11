package org.kyf37.dialer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ContentValues;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.CallLog;
import android.provider.ContactsContract;
import android.telecom.TelecomManager;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;

/** Call log: All / Missed / Dialed / Received / Frequent. Left/Right change the filter, digits jump to a row. */
public final class RecentsActivity extends Activity {
    private static final String[] MODES = { "All", "Missed", "Dialed", "Received", "Frequent" };

    private static final class Entry {
        long id; String number; String name; long date; int type; long duration; int count;
    }

    private KUi.Screen screen;
    private ListView list;
    private int mode;
    private final ArrayList<Entry> entries = new ArrayList<Entry>();

    private final KUi.Rows adapter = new KUi.Rows(this, false) {
        @Override public int getCount() { return entries.size(); }
        @Override protected KUi.Row row(int pos) {
            Entry e = entries.get(pos);
            KUi.Row r = new KUi.Row();
            r.num = pos < 9 ? String.valueOf(pos + 1) : "";
            r.title = e.name != null && e.name.length() > 0 ? e.name : (e.number == null || e.number.length() == 0 ? "Unknown" : e.number);
            r.bold = e.type == CallLog.Calls.MISSED_TYPE;
            if (e.type == CallLog.Calls.MISSED_TYPE) r.titleColor = KUi.RED;
            String tag = mode == 4 ? e.count + " calls" : typeName(e.type) + (e.duration > 0 ? "  " + KUi.duration(e.duration) : "");
            r.sub = (e.name != null && e.name.length() > 0 ? e.number + "   " : "") + tag;
            r.right = KUi.when(RecentsActivity.this, e.date);
            return r;
        }
    };

    static String typeName(int t) {
        switch (t) {
            case CallLog.Calls.INCOMING_TYPE: return "Received";
            case CallLog.Calls.OUTGOING_TYPE: return "Dialed";
            case CallLog.Calls.MISSED_TYPE: return "Missed";
            case CallLog.Calls.REJECTED_TYPE: return "Rejected";
            case CallLog.Calls.VOICEMAIL_TYPE: return "Voicemail";
            case CallLog.Calls.BLOCKED_TYPE: return "Blocked";
            default: return "Call";
        }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Recents");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { actions(pos); }
        });
        screen.body.addView(list);
        mode = 0;
        updateTitle();
    }

    @Override protected void onResume() {
        super.onResume();
        KUi.forgetNames();
        load();
        markRead();
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    private void updateTitle() {
        screen.setTitle("< " + MODES[mode] + " >");
        screen.hints("F1 Menu", "OK  Actions", "Call  Dial");
    }

    private void load() {
        entries.clear();
        Cursor c = null;
        try {
            String sel = null;
            if (mode == 1) sel = CallLog.Calls.TYPE + "=" + CallLog.Calls.MISSED_TYPE;
            else if (mode == 2) sel = CallLog.Calls.TYPE + "=" + CallLog.Calls.OUTGOING_TYPE;
            else if (mode == 3) sel = CallLog.Calls.TYPE + "=" + CallLog.Calls.INCOMING_TYPE;
            c = getContentResolver().query(CallLog.Calls.CONTENT_URI, new String[] {
                    CallLog.Calls._ID, CallLog.Calls.NUMBER, CallLog.Calls.CACHED_NAME, CallLog.Calls.DATE,
                    CallLog.Calls.TYPE, CallLog.Calls.DURATION }, sel, null, CallLog.Calls.DATE + " DESC LIMIT 500");
            while (c != null && c.moveToNext()) {
                Entry e = new Entry();
                e.id = c.getLong(0); e.number = c.getString(1); e.name = c.getString(2);
                e.date = c.getLong(3); e.type = c.getInt(4); e.duration = c.getLong(5); e.count = 1;
                if (e.name == null || e.name.length() == 0) e.name = KUi.nameFor(this, e.number);
                entries.add(e);
            }
        } catch (RuntimeException ex) {
            // no permission or provider: show an empty list
        } finally {
            if (c != null) c.close();
        }
        if (mode == 4) {
            HashMap<String, Entry> byNumber = new HashMap<String, Entry>();
            for (Entry e : entries) {
                if (e.number == null || e.number.length() == 0) continue;
                Entry f = byNumber.get(e.number);
                if (f == null) { byNumber.put(e.number, e); } else { f.count++; }
            }
            entries.clear();
            entries.addAll(byNumber.values());
            Collections.sort(entries, new Comparator<Entry>() {
                @Override public int compare(Entry a, Entry b) { return b.count != a.count ? b.count - a.count : Long.compare(b.date, a.date); }
            });
        }
        adapter.notifyDataSetChanged();
        if (!entries.isEmpty()) list.setSelection(0);
    }

    private void markRead() {
        try {
            ContentValues v = new ContentValues();
            v.put(CallLog.Calls.NEW, 0);
            v.put(CallLog.Calls.IS_READ, 1);
            getContentResolver().update(CallLog.Calls.CONTENT_URI, v, CallLog.Calls.TYPE + "=" + CallLog.Calls.MISSED_TYPE + " AND " + CallLog.Calls.NEW + "=1", null);
        } catch (RuntimeException e) {
            // ignore
        }
    }

    private Entry selected() {
        int p = list.getSelectedItemPosition();
        return p >= 0 && p < entries.size() ? entries.get(p) : null;
    }

    private void call(Entry e) {
        if (e == null || e.number == null || e.number.length() == 0) { KUi.toast(this, "Number unknown"); return; }
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", e.number, null), new Bundle());
        } catch (RuntimeException ex) {
            KUi.toast(this, "Cannot place call");
        }
    }

    private void actions(final int pos) {
        if (pos < 0 || pos >= entries.size()) return;
        final Entry e = entries.get(pos);
        final boolean known = e.name != null && e.name.length() > 0;
        String[] items = { "Call", "Send message", known ? "View contact" : "Save to contacts", "Delete this entry", "Delete all calls" };
        KUi.menu(this, KUi.nameOrNumber(this, e.number), items, new KUi.Pick() {
            @Override public void pick(int i) {
                switch (i) {
                    case 0: call(e); break;
                    case 1: start(new Intent(Intent.ACTION_SENDTO, Uri.fromParts("smsto", e.number, null))); break;
                    case 2: {
                        Intent in;
                        if (known) {
                            in = new Intent(Intent.ACTION_VIEW, ContactsContract.Contacts.CONTENT_URI);
                            in.putExtra("org.kyf37.contacts.SEARCH", e.name);
                        } else {
                            in = new Intent(Intent.ACTION_INSERT_OR_EDIT);
                            in.setType(ContactsContract.Contacts.CONTENT_ITEM_TYPE);
                            in.putExtra(ContactsContract.Intents.Insert.PHONE, e.number);
                        }
                        start(in); break; }
                    case 3:
                        KUi.confirm(RecentsActivity.this, "Delete", "Delete this call from the log?", "Delete", new Runnable() {
                            @Override public void run() {
                                try { getContentResolver().delete(CallLog.Calls.CONTENT_URI, CallLog.Calls._ID + "=" + e.id, null); }
                                catch (RuntimeException ex) { KUi.toast(RecentsActivity.this, "Cannot delete"); }
                                load();
                            }
                        });
                        break;
                    case 4:
                        KUi.confirmTwice(RecentsActivity.this, "Delete all calls", "Delete all", new Runnable() {
                            @Override public void run() {
                                try { getContentResolver().delete(CallLog.Calls.CONTENT_URI, null, null); }
                                catch (RuntimeException ex) { KUi.toast(RecentsActivity.this, "Cannot delete"); }
                                load();
                            }
                        });
                        break;
                    default: break;
                }
            }
        });
    }

    private void start(Intent i) {
        try { startActivity(i); } catch (ActivityNotFoundException ex) { KUi.toast(this, "Not available"); }
    }

    private void setMode(int m) {
        mode = (m + MODES.length) % MODES.length;
        updateTitle();
        load();
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0) {
            if (code == KeyEvent.KEYCODE_DPAD_LEFT) { setMode(mode - 1); return true; }
            if (code == KeyEvent.KEYCODE_DPAD_RIGHT) { setMode(mode + 1); return true; }
            if (code == KeyEvent.KEYCODE_CALL) { call(selected()); return true; }
            if (KUi.isMenuKey(code)) { actions(list.getSelectedItemPosition()); return true; }
            int d = KUi.digit(code);
            if (d >= 1 && d <= 9 && d - 1 < entries.size()) {
                list.setSelection(d - 1);
                actions(d - 1);
                return true;
            }
        }
        return super.onKeyDown(code, ev);
    }
}
