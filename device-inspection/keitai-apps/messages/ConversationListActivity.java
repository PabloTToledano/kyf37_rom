package org.kyf37.messages;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.telecom.TelecomManager;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import java.util.ArrayList;

/** Numbered conversation list. Digits open that conversation, OK opens the selected one, F1 = menu, Call = call. */
public final class ConversationListActivity extends Activity {
    private KUi.Screen screen;
    private ListView list;
    private final ArrayList<Msgs.Conv> convs = new ArrayList<Msgs.Conv>();

    private final KUi.Rows adapter = new KUi.Rows(this, true) {
        @Override public int getCount() { return convs.size(); }
        @Override protected KUi.Row row(int pos) {
            Msgs.Conv t = convs.get(pos);
            KUi.Row r = new KUi.Row();
            r.num = pos < 9 ? String.valueOf(pos + 1) : (pos == 9 ? "0" : "");
            r.title = t.title;
            r.bold = t.unread;
            r.sub = t.error ? "Failed - " + t.snippet : t.snippet;
            r.right = KUi.when(ConversationListActivity.this, t.date);
            r.rightColor = t.unread ? KUi.accent(ConversationListActivity.this) : KUi.TEXT2;
            r.avatar = KUi.initial(KUi.nameFor(ConversationListActivity.this, t.number.split(",")[0]) != null ? t.title : "#");
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Messages");
        screen.hints("F1 Menu", "OK  Open", "Call  Call");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { open(pos); }
        });
        screen.body.addView(list);
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

    private void reload() {
        int keep = list.getSelectedItemPosition();
        convs.clear();
        convs.addAll(Msgs.threads(this));
        adapter.notifyDataSetChanged();
        int unread = 0;
        for (Msgs.Conv c : convs) if (c.unread) unread++;
        screen.setTitle(unread > 0 ? "Messages (" + unread + " new)" : "Messages");
        if (!convs.isEmpty()) list.setSelection(Math.max(0, Math.min(keep, convs.size() - 1)));
    }

    private void open(int pos) {
        if (pos < 0 || pos >= convs.size()) return;
        startActivity(new Intent(this, ThreadActivity.class).putExtra("thread_id", convs.get(pos).id));
    }

    private void menu() {
        final int pos = list.getSelectedItemPosition();
        String[] items = { "New message", "Delete conversation", "Mark all as read", "Delete all conversations", "Settings" };
        KUi.menu(this, "Messages menu", items, new KUi.Pick() {
            @Override public void pick(int i) {
                switch (i) {
                    case 0: startActivity(new Intent(ConversationListActivity.this, ThreadActivity.class)); break;
                    case 1: deleteOne(pos); break;
                    case 2:
                        for (Msgs.Conv c : convs) if (c.unread) Msgs.markThreadRead(ConversationListActivity.this, c.id);
                        reload();
                        break;
                    case 3:
                        KUi.confirmTwice(ConversationListActivity.this, "Delete all conversations", "Delete all", new Runnable() {
                            @Override public void run() { Msgs.deleteAll(ConversationListActivity.this); reload(); }
                        });
                        break;
                    case 4: startActivity(new Intent(ConversationListActivity.this, SettingsActivity.class)); break;
                    default: break;
                }
            }
        });
    }

    private void deleteOne(int pos) {
        if (pos < 0 || pos >= convs.size()) return;
        final Msgs.Conv c = convs.get(pos);
        KUi.confirmTwice(this, "Delete conversation with " + c.title, "Delete", new Runnable() {
            @Override public void run() { Msgs.deleteThread(ConversationListActivity.this, c.id); reload(); }
        });
    }

    private void call(int pos) {
        if (pos < 0 || pos >= convs.size()) return;
        String n = convs.get(pos).number.split(",")[0];
        if (n.length() == 0) return;
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", n, null), new Bundle());
        } catch (RuntimeException e) { KUi.toast(this, "Cannot place call"); }
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0) {
            if (KUi.isMenuKey(code)) { menu(); return true; }
            if (code == KeyEvent.KEYCODE_CALL) { call(list.getSelectedItemPosition()); return true; }
            int d = KUi.digit(code);
            if (d >= 0) {
                int row = d == 0 ? 9 : d - 1;
                if (row < convs.size()) { list.setSelection(row); open(row); }
                return true;
            }
        }
        return super.onKeyDown(code, ev);
    }
}
