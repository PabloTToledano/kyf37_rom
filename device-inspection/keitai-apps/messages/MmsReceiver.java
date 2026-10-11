package org.kyf37.messages;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.provider.Telephony;
import java.io.File;

/**
 * WAP_PUSH_DELIVER (protected by BROADCAST_WAP_PUSH in the manifest): a new MMS notification. We record it, then ask the
 * platform MmsService to download it. Status is the (unprotected) result receiver for downloads and sends.
 */
public class MmsReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        if (!Telephony.Sms.Intents.WAP_PUSH_DELIVER_ACTION.equals(i.getAction())) return;
        byte[] data = i.getByteArrayExtra("data");
        if (data == null) return;
        int[] at = new int[1];
        Mms.Pdu n = Mms.parse(data, at);
        if (n.type != 130 || n.location.length() == 0) return; // only m-notification-ind
        long row = Mms.storeNotification(c, n);
        Msgs.notifyIncoming(c, row > 0 ? threadOf(c, row) : -1, n.from, "Multimedia message" + (n.subject.length() > 0 ? ": " + n.subject : ""));
        Mms.download(c, n, row);
    }

    private static long threadOf(Context c, long mmsRow) {
        android.database.Cursor cur = null;
        try {
            cur = c.getContentResolver().query(ContentUris.withAppendedId(Telephony.Mms.CONTENT_URI, mmsRow), new String[] { "thread_id" }, null, null, null);
            if (cur != null && cur.moveToFirst()) return cur.getLong(0);
        } catch (RuntimeException e) {
            // ignore
        } finally {
            if (cur != null) cur.close();
        }
        return -1;
    }

    public static final class Status extends BroadcastReceiver {
        @Override public void onReceive(Context c, Intent i) {
            String a = i.getAction();
            String name = i.getStringExtra("file");
            if (a == null || name == null) return;
            File f = new File(Mms.dir(c), name);
            try {
                if (Mms.ACTION_DOWNLOADED.equals(a)) {
                    if (Mms.ok(getResultCode()) && f.length() > 0) {
                        Mms.Pdu m = Mms.parseRetrieveConf(Mms.readFile(f));
                        if (m.from.length() == 0) m.from = i.getStringExtra("from") == null ? "" : i.getStringExtra("from");
                        if (m.subject.length() == 0 && i.getStringExtra("subject") != null) m.subject = i.getStringExtra("subject");
                        if (m.transactionId.length() == 0) m.transactionId = i.getStringExtra("tr_id") == null ? "" : i.getStringExtra("tr_id");
                        long t = Mms.storeInbox(c, m, i.getLongExtra("notif_row", -1));
                        StringBuilder text = new StringBuilder();
                        for (Mms.Part p : m.parts) if (p.ct.startsWith("text/plain")) text.append(new String(p.data, "UTF-8"));
                        Msgs.notifyIncoming(c, t, m.from, text.length() > 0 ? text.toString() : "Multimedia message");
                    }
                } else if (Mms.ACTION_SENT.equals(a)) {
                    ContentValues v = new ContentValues();
                    v.put("msg_box", Mms.ok(getResultCode()) ? 2 : 5);
                    c.getContentResolver().update(ContentUris.withAppendedId(Telephony.Mms.CONTENT_URI, i.getLongExtra("row", -1)), v, null, null);
                }
            } catch (Exception e) {
                // leave the notification row in place
            } finally {
                f.delete();
            }
        }
    }
}
