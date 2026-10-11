package org.kyf37.messages;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.database.ContentObserver;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.provider.ContactsContract;
import android.telecom.TelecomManager;
import android.telephony.SmsMessage;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import java.util.ArrayList;

/**
 * One conversation plus the compose box, also the "new message" screen (when no recipient is known an extra To field
 * is shown). Handles SENDTO sms/smsto/mms/mmsto, SEND text/plain, and the notification Reply button.
 * List: Up/Down select, OK = message actions. Down from the last message goes to the text box, Down again to Send.
 */
public final class ThreadActivity extends Activity {
    private static final int REQ_PICK = 11;
    private static final String[] QUICK = { "OK", "Yes", "No", "On my way.", "Call me later.", "Thanks!", "I'm busy right now." };

    private KUi.Screen screen;
    private ListView list;
    private EditText toField, body;
    private TextView sendBtn;
    private LinearLayout toRow;
    private long threadId;
    private final ArrayList<String> recipients = new ArrayList<String>();
    private final ArrayList<Msgs.Msg> msgs = new ArrayList<Msgs.Msg>();
    private final Handler handler = new Handler();
    private boolean focusCompose;

    private final ContentObserver observer = new ContentObserver(new Handler()) {
        @Override public void onChange(boolean self) { handler.removeCallbacks(refreshTask); handler.postDelayed(refreshTask, 150); }
    };
    private final Runnable refreshTask = new Runnable() { @Override public void run() { reload(false); } };

    private final KUi.Rows adapter = new KUi.Rows(this, false) {
        @Override public int getCount() { return msgs.size(); }
        @Override protected KUi.Row row(int pos) {
            Msgs.Msg m = msgs.get(pos);
            KUi.Row r = new KUi.Row();
            boolean in = m.incoming();
            r.num = in ? "<" : ">";
            r.numColor = in ? KUi.TEXT2 : KUi.accent(ThreadActivity.this);
            r.title = m.body.length() == 0 ? "(empty)" : m.body;
            r.titleLines = 6;
            r.titleColor = in ? Color.WHITE : 0xFFDDE8F5;
            String when = KUi.when(ThreadActivity.this, m.date);
            String st = "";
            if (!in) {
                switch (m.type) {
                    case 4: case 6: st = "  Sending..."; break;
                    case 5: st = "  Failed - OK to retry"; r.rightColor = KUi.RED; break;
                    case 2: st = m.status == 0 ? "  Delivered" : m.status == 64 ? "  Delivery failed" : "  Sent"; break;
                    default: break;
                }
            } else if (recipients.size() > 1 && m.address.length() > 0) {
                st = "  " + KUi.nameOrNumber(ThreadActivity.this, m.address);
            }
            r.sub = when + st + (m.mms ? "  MMS" : "");
            if (!in && m.type == 5) r.sub = when + st;
            return r;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE | WindowManager.LayoutParams.SOFT_INPUT_STATE_HIDDEN);
        screen = KUi.screen(this, "New message");
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);

        toRow = new LinearLayout(this);
        toRow.setOrientation(LinearLayout.HORIZONTAL);
        toRow.setGravity(Gravity.CENTER_VERTICAL);
        toRow.setPadding(KUi.px(this, 10), KUi.px(this, 4), KUi.px(this, 10), KUi.px(this, 4));
        TextView toLabel = new TextView(this);
        toLabel.setText("To:");
        toLabel.setTextSize(16);
        toLabel.setTextColor(KUi.accent(this));
        toRow.addView(toLabel);
        toField = styled(new EditText(this));
        toField.setSingleLine(true);
        toField.setHint("number");
        toField.setInputType(InputType.TYPE_CLASS_PHONE);
        LinearLayout.LayoutParams tlp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        tlp.leftMargin = KUi.px(this, 8);
        toRow.addView(toField, tlp);
        col.addView(toRow, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        list = KUi.list(this);
        list.setAdapter(adapter);
        list.setStackFromBottom(true);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { actions(pos); }
        });
        col.addView(list, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout compose = new LinearLayout(this);
        compose.setOrientation(LinearLayout.HORIZONTAL);
        compose.setGravity(Gravity.CENTER_VERTICAL);
        compose.setBackgroundColor(0xFF0B0F13);
        compose.setPadding(KUi.px(this, 8), KUi.px(this, 4), KUi.px(this, 8), KUi.px(this, 4));
        body = styled(new EditText(this));
        body.setHint("Write a message");
        body.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        body.setMaxLines(3);
        compose.addView(body, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        sendBtn = new TextView(this);
        sendBtn.setText("Send");
        sendBtn.setTextSize(16);
        sendBtn.setTypeface(Typeface.DEFAULT_BOLD);
        sendBtn.setTextColor(Color.WHITE);
        sendBtn.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setColor(KUi.headerColor(this));
        g.setCornerRadius(KUi.px(this, 8));
        sendBtn.setBackground(g);
        sendBtn.setFocusable(true);
        sendBtn.setClickable(true);
        sendBtn.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { send(); } });
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(KUi.px(this, 64), KUi.px(this, 44));
        slp.leftMargin = KUi.px(this, 6);
        compose.addView(sendBtn, slp);
        col.addView(compose, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        screen.body.addView(col);

        View.OnFocusChangeListener hints = new View.OnFocusChangeListener() {
            @Override public void onFocusChange(View v, boolean has) { if (has) updateHints(v); }
        };
        body.setOnFocusChangeListener(hints);
        toField.setOnFocusChangeListener(hints);
        sendBtn.setOnFocusChangeListener(hints);
        list.setOnFocusChangeListener(hints);

        parse(getIntent());
        getContentResolver().registerContentObserver(Uri.parse("content://mms-sms/"), true, observer);
    }

    private EditText styled(EditText e) {
        e.setTextSize(17);
        e.setTextColor(Color.WHITE);
        e.setHintTextColor(0xFF5B6773);
        GradientDrawable g = new GradientDrawable();
        g.setColor(0xFF1B2430);
        g.setStroke(1, 0xFF3A4654);
        g.setCornerRadius(KUi.px(this, 6));
        e.setBackground(g);
        e.setPadding(KUi.px(this, 8), KUi.px(this, 6), KUi.px(this, 8), KUi.px(this, 6));
        return e;
    }

    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        setIntent(i);
        parse(i);
    }

    private void parse(Intent in) {
        recipients.clear();
        threadId = in.getLongExtra("thread_id", 0);
        focusCompose = in.getBooleanExtra("focus_compose", false);
        Uri d = in.getData();
        if (d != null && d.getScheme() != null && d.getScheme().matches("sms|smsto|mms|mmsto")) {
            String to = d.getSchemeSpecificPart();
            int q = to.indexOf('?');
            if (q >= 0) to = to.substring(0, q);
            addRecipients(Uri.decode(to));
        }
        String a = in.getStringExtra("address");
        if (a != null) addRecipients(a);
        String text = in.getStringExtra("sms_body");
        if (text == null) text = in.getStringExtra(Intent.EXTRA_TEXT);
        if (text != null && body.getText().length() == 0) { body.setText(text); body.setSelection(body.length()); focusCompose = true; }
        if (threadId > 0 && recipients.isEmpty()) {
            Msgs.Conv c = Msgs.thread(this, threadId);
            if (c != null) addRecipients(c.number);
        } else if (threadId <= 0 && recipients.size() == 1) {
            try { threadId = Msgs.threadFor(this, recipients.get(0)); } catch (RuntimeException e) { threadId = 0; }
        }
        reload(true);
    }

    private void addRecipients(String s) {
        for (String p : s.split("[,;]")) {
            p = p.trim();
            if (p.length() > 0 && !recipients.contains(p)) recipients.add(p);
        }
    }

    @Override protected void onResume() {
        super.onResume();
        KUi.forgetNames();
        if (threadId > 0) Msgs.markThreadRead(this, threadId);
        reload(false);
    }

    @Override protected void onDestroy() {
        getContentResolver().unregisterContentObserver(observer);
        screen.unwatch();
        super.onDestroy();
    }

    private void reload(boolean first) {
        boolean newThread = recipients.isEmpty();
        toRow.setVisibility(newThread ? View.VISIBLE : View.GONE);
        msgs.clear();
        if (threadId > 0) msgs.addAll(Msgs.messages(this, threadId));
        adapter.notifyDataSetChanged();
        if (newThread) screen.setTitle("New message");
        else {
            StringBuilder t = new StringBuilder();
            for (String r : recipients) { if (t.length() > 0) t.append(", "); t.append(KUi.nameOrNumber(this, r)); }
            screen.setTitle(t.toString());
        }
        if (first || list.getSelectedItemPosition() < 0) {
            if (!msgs.isEmpty()) list.setSelection(msgs.size() - 1);
            View f = focusCompose ? body : (newThread ? toField : (msgs.isEmpty() ? body : list));
            f.requestFocus();
            updateHints(f);
        } else if (first == false && !msgs.isEmpty() && list.hasFocus() && list.getSelectedItemPosition() >= msgs.size()) {
            list.setSelection(msgs.size() - 1);
        }
    }

    private void updateHints(View focus) {
        if (focus == body) screen.hints("F1 Menu", "Down  Send", "Clear  Delete");
        else if (focus == toField) screen.hints("F1 Menu", "Down  Message", "Clear  Delete");
        else if (focus == sendBtn) screen.hints("F1 Menu", "OK  Send", "Clear  Back");
        else screen.hints("F1 Menu", "OK  Options", "Call  Call");
    }

    // ------------------------------------------------------------------------------------------ sending

    private void send() {
        String text = body.getText().toString();
        if (text.trim().length() == 0) { KUi.toast(this, "Write a message first"); body.requestFocus(); return; }
        if (recipients.isEmpty()) {
            addRecipients(toField.getText().toString());
            if (recipients.isEmpty()) { KUi.toast(this, "Enter a number"); toField.requestFocus(); return; }
        }
        try {
            Uri first = null;
            for (String r : recipients) {
                Uri u = Msgs.send(this, r, text);
                if (first == null) first = u;
            }
            if (first == null) { KUi.toast(this, "Could not store the message"); return; }
            if (threadId <= 0 || recipients.size() > 1) {
                if (recipients.size() == 1) threadId = Msgs.threadFor(this, recipients.get(0));
                else { finish(); return; }
            }
            body.setText("");
            reload(true);
            list.requestFocus();
        } catch (SecurityException e) {
            KUi.toast(this, "Sending texts is not permitted");
        } catch (RuntimeException e) {
            KUi.toast(this, "Could not send");
        }
    }

    /** Text-only MMS through the platform MmsService (needs mobile data + APN; not testable without a radio). */
    private void sendMms() {
        String text = body.getText().toString();
        if (text.trim().length() == 0) { KUi.toast(this, "Write a message first"); return; }
        if (recipients.isEmpty()) addRecipients(toField.getText().toString());
        if (recipients.isEmpty()) { KUi.toast(this, "Enter a number"); toField.requestFocus(); return; }
        try {
            Mms.sendText(this, new ArrayList<String>(recipients), text);
            if (threadId <= 0 && recipients.size() == 1) threadId = Msgs.threadFor(this, recipients.get(0));
            body.setText("");
            reload(true);
        } catch (Exception e) {
            KUi.toast(this, "Could not send the MMS");
        }
    }

    // ------------------------------------------------------------------------------------------ actions

    private void actions(int pos) {
        if (pos < 0 || pos >= msgs.size()) return;
        final Msgs.Msg m = msgs.get(pos);
        final ArrayList<String> labels = new ArrayList<String>();
        final ArrayList<String> ids = new ArrayList<String>();
        if (!m.incoming() && m.type == 5 && !m.mms) { labels.add("Send again"); ids.add("resend"); }
        labels.add("Reply"); ids.add("reply");
        labels.add("Forward"); ids.add("forward");
        labels.add("Copy text"); ids.add("copy");
        if (m.incoming() && m.address.length() > 0) { labels.add("Call sender"); ids.add("call"); }
        labels.add("Delete"); ids.add("delete");
        labels.add("Details"); ids.add("details");
        KUi.menu(this, "Message", labels.toArray(new String[0]), new KUi.Pick() {
            @Override public void pick(int i) {
                String id = ids.get(i);
                if ("resend".equals(id)) { Msgs.resend(ThreadActivity.this, m); }
                else if ("reply".equals(id)) { body.requestFocus(); }
                else if ("forward".equals(id)) {
                    Intent f = new Intent(ThreadActivity.this, ThreadActivity.class).putExtra("sms_body", m.body).putExtra("thread_id", 0L);
                    f.setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, m.body);
                    startActivity(f);
                }
                else if ("copy".equals(id)) {
                    ((ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("message", m.body));
                    KUi.toast(ThreadActivity.this, "Copied");
                }
                else if ("call".equals(id)) callNumber(m.address);
                else if ("delete".equals(id)) {
                    KUi.confirm(ThreadActivity.this, "Delete", "Delete this message?", "Delete", new Runnable() {
                        @Override public void run() { Msgs.deleteMessage(ThreadActivity.this, m); reload(false); }
                    });
                }
                else if ("details".equals(id)) {
                    String det = (m.incoming() ? "From: " : "To: ") + (m.address.length() > 0 ? m.address : (recipients.isEmpty() ? "" : recipients.get(0)))
                            + "\nTime: " + new java.text.SimpleDateFormat("d MMM yyyy HH:mm:ss").format(new java.util.Date(m.date))
                            + "\nType: " + (m.mms ? "MMS" : "SMS") + "\nLength: " + m.body.length() + " characters"
                            + (m.mms ? "" : ", " + SmsMessage.calculateLength(m.body, false)[0] + " part(s)");
                    new android.app.AlertDialog.Builder(ThreadActivity.this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                            .setTitle("Details").setMessage(det).setPositiveButton("OK", null).show();
                }
            }
        });
    }

    private void callNumber(String n) {
        if (n == null || n.length() == 0) return;
        try {
            ((TelecomManager) getSystemService(TELECOM_SERVICE)).placeCall(Uri.fromParts("tel", n, null), new Bundle());
        } catch (RuntimeException e) { KUi.toast(this, "Cannot place call"); }
    }

    private void menu() {
        final ArrayList<String> labels = new ArrayList<String>();
        final ArrayList<String> ids = new ArrayList<String>();
        if (body.getText().length() > 0) { labels.add("Send"); ids.add("send"); labels.add("Send as MMS (text)"); ids.add("mms"); }
        if (!recipients.isEmpty()) { labels.add("Call"); ids.add("call"); }
        labels.add("Quick text"); ids.add("quick");
        if (recipients.isEmpty()) { labels.add("Choose from contacts"); ids.add("pick"); }
        if (!recipients.isEmpty() && KUi.nameFor(this, recipients.get(0)) == null) { labels.add("Save number to contacts"); ids.add("save"); }
        if (threadId > 0) { labels.add("Delete conversation"); ids.add("delete"); }
        KUi.menu(this, "Message menu", labels.toArray(new String[0]), new KUi.Pick() {
            @Override public void pick(int i) {
                String id = ids.get(i);
                if ("send".equals(id)) send();
                else if ("mms".equals(id)) sendMms();
                else if ("call".equals(id)) callNumber(recipients.get(0));
                else if ("quick".equals(id)) {
                    KUi.menu(ThreadActivity.this, "Quick text", QUICK, new KUi.Pick() {
                        @Override public void pick(int j) { body.append(QUICK[j]); body.requestFocus(); }
                    });
                }
                else if ("pick".equals(id)) {
                    try { startActivityForResult(new Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI), REQ_PICK); }
                    catch (ActivityNotFoundException e) { KUi.toast(ThreadActivity.this, "No contacts app"); }
                }
                else if ("save".equals(id)) {
                    Intent in = new Intent(Intent.ACTION_INSERT_OR_EDIT).setType(ContactsContract.Contacts.CONTENT_ITEM_TYPE);
                    in.putExtra(ContactsContract.Intents.Insert.PHONE, recipients.get(0));
                    try { startActivity(in); } catch (ActivityNotFoundException e) { KUi.toast(ThreadActivity.this, "No contacts app"); }
                }
                else if ("delete".equals(id)) {
                    KUi.confirmTwice(ThreadActivity.this, "Delete this conversation", "Delete", new Runnable() {
                        @Override public void run() { Msgs.deleteThread(ThreadActivity.this, threadId); finish(); }
                    });
                }
            }
        });
    }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        if (req != REQ_PICK || res != RESULT_OK || data == null || data.getData() == null) return;
        Cursor c = null;
        try {
            c = getContentResolver().query(data.getData(), new String[] { ContactsContract.CommonDataKinds.Phone.NUMBER }, null, null, null);
            if (c != null && c.moveToFirst()) {
                String cur = toField.getText().toString().trim();
                toField.setText(cur.length() == 0 ? c.getString(0) : cur + ", " + c.getString(0));
                toField.setSelection(toField.length());
                body.requestFocus();
            }
        } catch (RuntimeException e) {
            KUi.toast(this, "Could not read the contact");
        } finally {
            if (c != null) c.close();
        }
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        if (ev.getRepeatCount() == 0) {
            if (KUi.isMenuKey(code)) { menu(); return true; }
            if (code == KeyEvent.KEYCODE_CALL) {
                if (!recipients.isEmpty()) callNumber(recipients.get(0));
                else if (toField.getText().length() > 0) callNumber(toField.getText().toString().trim());
                return true;
            }
        }
        return super.onKeyDown(code, ev);
    }
}
