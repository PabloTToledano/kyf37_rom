package org.kyf37.messages;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.Telephony;
import android.telephony.SmsMessage;

/** SMS_DELIVER: the default-SMS-app contract. Protected by BROADCAST_SMS in the manifest (only the platform can send it). */
public class SmsReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        if (!Telephony.Sms.Intents.SMS_DELIVER_ACTION.equals(i.getAction())) return;
        SmsMessage[] msgs = Telephony.Sms.Intents.getMessagesFromIntent(i);
        if (msgs == null || msgs.length == 0 || msgs[0] == null) return;
        StringBuilder body = new StringBuilder();
        for (SmsMessage m : msgs) if (m != null && m.getDisplayMessageBody() != null) body.append(m.getDisplayMessageBody());
        String from = msgs[0].getDisplayOriginatingAddress();
        store(c, from == null ? "" : from, body.toString(), System.currentTimeMillis(), msgs[0].getTimestampMillis());
    }

    /** Writes an incoming text to the provider and raises the notification. Also used by the debug hook. */
    static void store(Context c, String from, String body, long date, long dateSent) {
        Uri u = Msgs.insertIncoming(c, from, body, date, dateSent);
        if (u == null) return;
        long thread = -1;
        android.database.Cursor cur = null;
        try {
            cur = c.getContentResolver().query(u, new String[] { "thread_id" }, null, null, null);
            if (cur != null && cur.moveToFirst()) thread = cur.getLong(0);
        } catch (RuntimeException e) {
            thread = -1;
        } finally {
            if (cur != null) cur.close();
        }
        Msgs.notifyIncoming(c, thread, from, body);
    }
}
