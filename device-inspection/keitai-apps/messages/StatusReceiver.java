package org.kyf37.messages;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Telephony;

/**
 * Not exported, no permission: sent / delivered results of our own outgoing texts, the notification "Mark read" button,
 * and (non-"user" builds only, via the exported Debug subclass entry) a fake incoming text.
 */
public class StatusReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        String a = i.getAction();
        if (a == null) return;
        switch (a) {
            case Msgs.ACTION_SENT: sent(c, i); break;
            case Msgs.ACTION_DELIVERED: delivered(c, i); break;
            case Msgs.ACTION_MARK_READ: Msgs.markThreadRead(c, i.getLongExtra("thread_id", -1)); break;
            default: break;
        }
    }

    private void sent(Context c, Intent i) {
        Uri u = i.getData();
        if (u == null) return;
        if (getResultCode() == Activity.RESULT_OK) {
            ContentValues v = new ContentValues();
            v.put("type", Telephony.Sms.MESSAGE_TYPE_SENT);
            // do not overwrite a failure reported by an earlier part of the same message
            c.getContentResolver().update(u, v, "type != ?", new String[] { String.valueOf(Telephony.Sms.MESSAGE_TYPE_FAILED) });
        } else {
            Msgs.fail(c, u, getResultCode());
        }
    }

    private void delivered(Context c, Intent i) {
        Uri u = i.getData();
        if (u == null) return;
        ContentValues v = new ContentValues();
        v.put("status", getResultCode() == Activity.RESULT_OK ? Telephony.Sms.STATUS_COMPLETE : Telephony.Sms.STATUS_FAILED);
        v.put("date_sent", System.currentTimeMillis());
        c.getContentResolver().update(u, v, null, null);
    }

    /**
     * DEBUG ONLY: adb shell am broadcast -a org.kyf37.messages.DEBUG_RECEIVE --es from 600123456 --es body "hi" -n org.kyf37.messages/.StatusReceiver\$Debug
     * Ignored on "user" builds. Exercises the same storage + notification path as a real SMS_DELIVER.
     */
    public static final class Debug extends BroadcastReceiver {
        @Override public void onReceive(Context c, Intent i) {
            if ("user".equals(Build.TYPE) || !"org.kyf37.messages.DEBUG_RECEIVE".equals(i.getAction())) return;
            String from = i.getStringExtra("from") == null ? "600123456" : i.getStringExtra("from");
            String body = i.getStringExtra("body") == null ? "Test message" : i.getStringExtra("body");
            SmsReceiver.store(c, from, body, System.currentTimeMillis(), 0);
        }
    }
}
