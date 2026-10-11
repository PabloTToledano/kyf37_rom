package org.kyf37.messages;

import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;

/** Two switches: delivery reports and message notifications. Digit = toggle that row. */
public final class SettingsActivity extends Activity {
    private KUi.Screen screen;
    private ListView list;

    private final KUi.Rows adapter = new KUi.Rows(this, false) {
        @Override public int getCount() { return 2; }
        @Override protected KUi.Row row(int pos) {
            KUi.Row r = new KUi.Row();
            r.num = String.valueOf(pos + 1);
            if (pos == 0) { r.title = "Delivery reports"; r.sub = "Ask the network to confirm delivery"; r.right = Msgs.deliveryReports(SettingsActivity.this) ? "On" : "Off"; }
            else { r.title = "Notifications"; r.sub = "Show a notification for new messages"; r.right = Msgs.notifications(SettingsActivity.this) ? "On" : "Off"; }
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        screen = KUi.screen(this, "Message settings");
        screen.hints("", "OK  Switch", "Clear  Back");
        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { toggle(pos); }
        });
        screen.body.addView(list);
    }

    @Override protected void onDestroy() {
        screen.unwatch();
        super.onDestroy();
    }

    private void toggle(int pos) {
        String key = pos == 0 ? "delivery_reports" : "notifications";
        boolean cur = pos == 0 ? Msgs.deliveryReports(this) : Msgs.notifications(this);
        Msgs.prefs(this).edit().putBoolean(key, !cur).apply();
        adapter.notifyDataSetChanged();
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        int d = KUi.digit(code);
        if (ev.getRepeatCount() == 0 && d >= 1 && d <= 2) { list.setSelection(d - 1); toggle(d - 1); return true; }
        return super.onKeyDown(code, ev);
    }
}
