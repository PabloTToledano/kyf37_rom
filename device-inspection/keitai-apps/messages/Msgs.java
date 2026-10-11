package org.kyf37.messages;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.provider.Telephony;
import android.telephony.SmsManager;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;

/** Telephony provider access, SMS sending and notifications for the Messages app. */
final class Msgs {
    private Msgs() { }

    static final String CH_MESSAGES = "messages";
    static final String ACTION_SENT = "org.kyf37.messages.SENT";
    static final String ACTION_DELIVERED = "org.kyf37.messages.DELIVERED";
    static final String ACTION_MARK_READ = "org.kyf37.messages.MARK_READ";

    static final class Conv {
        long id; String title; String number; String snippet; long date; int count; boolean unread; boolean error;
    }

    static final class Msg {
        long id; boolean mms; String body = ""; long date; int type; int status = -1; boolean read; String address = "";
        int attachments; String subject;
        boolean incoming() { return type == Telephony.Sms.MESSAGE_TYPE_INBOX; }
    }

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences("messages", Context.MODE_PRIVATE); }
    static boolean deliveryReports(Context c) { return prefs(c).getBoolean("delivery_reports", false); }
    static boolean notifications(Context c) { return prefs(c).getBoolean("notifications", true); }

    // ----------------------------------------------------------------------------------------------- threads

    static HashMap<Long, String> canonical(Context c) {
        HashMap<Long, String> m = new HashMap<Long, String>();
        Cursor cur = null;
        try {
            cur = c.getContentResolver().query(Uri.parse("content://mms-sms/canonical-addresses"), new String[] { "_id", "address" }, null, null, null);
            while (cur != null && cur.moveToNext()) m.put(cur.getLong(0), cur.getString(1));
        } catch (RuntimeException e) {
            // empty
        } finally {
            if (cur != null) cur.close();
        }
        return m;
    }

    static ArrayList<Conv> threads(Context c) {
        ArrayList<Conv> out = new ArrayList<Conv>();
        HashMap<Long, String> addr = canonical(c);
        Cursor cur = null;
        try {
            Uri u = Telephony.Threads.CONTENT_URI.buildUpon().appendQueryParameter("simple", "true").build();
            cur = c.getContentResolver().query(u, new String[] { "_id", "date", "message_count", "recipient_ids", "snippet", "read", "error" },
                    null, null, "date DESC");
            while (cur != null && cur.moveToNext()) {
                Conv t = new Conv();
                t.id = cur.getLong(0); t.date = cur.getLong(1); t.count = cur.getInt(2);
                t.snippet = cur.getString(4) == null ? "" : cur.getString(4);
                t.unread = cur.getInt(5) == 0; t.error = cur.getInt(6) != 0;
                StringBuilder title = new StringBuilder(), num = new StringBuilder();
                String ids = cur.getString(3);
                if (ids != null) for (String s : ids.trim().split("\\s+")) {
                    if (s.length() == 0) continue;
                    String a = addr.get(Long.parseLong(s));
                    if (a == null) continue;
                    if (title.length() > 0) { title.append(", "); num.append(','); }
                    title.append(KUi.nameOrNumber(c, a));
                    num.append(a);
                }
                t.title = title.length() == 0 ? "(no recipient)" : title.toString();
                t.number = num.toString();
                if (t.count > 0 || t.snippet.length() > 0) out.add(t);
            }
        } catch (RuntimeException e) {
            // no permission or provider: empty list
        } finally {
            if (cur != null) cur.close();
        }
        return out;
    }

    static int unreadThreads(Context c) {
        int n = 0;
        for (Conv t : threads(c)) if (t.unread) n++;
        return n;
    }

    static Conv thread(Context c, long id) {
        for (Conv t : threads(c)) if (t.id == id) return t;
        return null;
    }

    // ----------------------------------------------------------------------------------------------- messages

    static ArrayList<Msg> messages(Context c, long threadId) {
        ArrayList<Msg> out = new ArrayList<Msg>();
        ContentResolver cr = c.getContentResolver();
        Cursor cur = null;
        try {
            cur = cr.query(Telephony.Sms.CONTENT_URI, new String[] { "_id", "address", "body", "date", "type", "status", "read" },
                    "thread_id=?", new String[] { String.valueOf(threadId) }, "date ASC, _id ASC");
            while (cur != null && cur.moveToNext()) {
                Msg m = new Msg();
                m.id = cur.getLong(0); m.address = cur.getString(1) == null ? "" : cur.getString(1);
                m.body = cur.getString(2) == null ? "" : cur.getString(2);
                m.date = cur.getLong(3); m.type = cur.getInt(4); m.status = cur.getInt(5); m.read = cur.getInt(6) != 0;
                out.add(m);
            }
        } catch (RuntimeException e) {
            // ignore
        } finally {
            if (cur != null) cur.close();
        }
        try {
            cur = cr.query(Telephony.Mms.CONTENT_URI, new String[] { "_id", "date", "msg_box", "sub", "read" },
                    "thread_id=?", new String[] { String.valueOf(threadId) }, "date ASC");
            while (cur != null && cur.moveToNext()) {
                Msg m = new Msg();
                m.mms = true;
                m.id = cur.getLong(0); m.date = cur.getLong(1) * 1000L;
                int box = cur.getInt(2);
                m.type = box == 1 ? Telephony.Sms.MESSAGE_TYPE_INBOX : box == 2 ? Telephony.Sms.MESSAGE_TYPE_SENT : Telephony.Sms.MESSAGE_TYPE_OUTBOX;
                m.subject = cur.getString(3); m.read = cur.getInt(4) != 0;
                mmsParts(c, m);
                out.add(m);
            }
        } catch (RuntimeException e) {
            // ignore
        } finally {
            if (cur != null) cur.close();
        }
        Collections.sort(out, new Comparator<Msg>() {
            @Override public int compare(Msg a, Msg b) { return Long.compare(a.date, b.date); }
        });
        return out;
    }

    private static void mmsParts(Context c, Msg m) {
        Cursor p = null;
        StringBuilder text = new StringBuilder();
        try {
            p = c.getContentResolver().query(Uri.parse("content://mms/" + m.id + "/part"), new String[] { "ct", "text", "name" }, null, null, "_id");
            while (p != null && p.moveToNext()) {
                String ct = p.getString(0);
                if ("text/plain".equals(ct)) { if (p.getString(1) != null) text.append(p.getString(1)); }
                else if (!"application/smil".equals(ct)) { m.attachments++; }
            }
        } catch (RuntimeException e) {
            // ignore
        } finally {
            if (p != null) p.close();
        }
        String body = text.toString();
        if (m.subject != null && m.subject.length() > 0) body = m.subject + (body.length() > 0 ? "\n" : "") + body;
        if (m.attachments > 0) body = body + (body.length() > 0 ? "\n" : "") + "[" + m.attachments + " attachment" + (m.attachments > 1 ? "s" : "") + " - not shown on this phone]";
        m.body = body;
    }

    static void markThreadRead(Context c, long threadId) {
        ContentValues v = new ContentValues();
        v.put("read", 1);
        v.put("seen", 1);
        try {
            c.getContentResolver().update(Telephony.Sms.CONTENT_URI, v, "thread_id=? AND read=0", new String[] { String.valueOf(threadId) });
            c.getContentResolver().update(Telephony.Mms.CONTENT_URI, v, "thread_id=? AND read=0", new String[] { String.valueOf(threadId) });
        } catch (RuntimeException e) {
            // ignore
        }
        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(notifId(threadId));
    }

    static void deleteThread(Context c, long threadId) {
        try {
            c.getContentResolver().delete(ContentUris.withAppendedId(Telephony.Threads.CONTENT_URI, threadId), null, null);
            c.getContentResolver().delete(Telephony.Sms.CONTENT_URI, "thread_id=?", new String[] { String.valueOf(threadId) });
        } catch (RuntimeException e) {
            // ignore
        }
        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(notifId(threadId));
    }

    static void deleteMessage(Context c, Msg m) {
        try {
            if (m.mms) c.getContentResolver().delete(ContentUris.withAppendedId(Telephony.Mms.CONTENT_URI, m.id), null, null);
            else c.getContentResolver().delete(ContentUris.withAppendedId(Telephony.Sms.CONTENT_URI, m.id), null, null);
        } catch (RuntimeException e) {
            // ignore
        }
    }

    static void deleteAll(Context c) {
        try {
            c.getContentResolver().delete(Telephony.Sms.CONTENT_URI, null, null);
            c.getContentResolver().delete(Telephony.Mms.CONTENT_URI, null, null);
        } catch (RuntimeException e) {
            // ignore
        }
    }

    // ----------------------------------------------------------------------------------------------- sending

    static long threadFor(Context c, String address) {
        return Telephony.Threads.getOrCreateThreadId(c, address);
    }

    /** Writes the message to the outbox and hands it to SmsManager. Returns the provider row. */
    static Uri send(Context c, String address, String body) {
        ContentValues v = new ContentValues();
        v.put("address", address);
        v.put("body", body);
        v.put("date", System.currentTimeMillis());
        v.put("read", 1);
        v.put("seen", 1);
        v.put("type", Telephony.Sms.MESSAGE_TYPE_OUTBOX);
        v.put("status", Telephony.Sms.STATUS_NONE);
        Uri u = c.getContentResolver().insert(Telephony.Sms.CONTENT_URI, v);
        if (u != null) dispatch(c, u, address, body);
        return u;
    }

    static void resend(Context c, Msg m) {
        ContentValues v = new ContentValues();
        v.put("type", Telephony.Sms.MESSAGE_TYPE_OUTBOX);
        v.put("date", System.currentTimeMillis());
        v.put("error_code", 0);
        Uri u = ContentUris.withAppendedId(Telephony.Sms.CONTENT_URI, m.id);
        c.getContentResolver().update(u, v, null, null);
        dispatch(c, u, m.address, m.body);
    }

    private static void dispatch(Context c, Uri u, String address, String body) {
        try {
            SmsManager sm = SmsManager.getDefault();
            ArrayList<String> parts = sm.divideMessage(body);
            boolean dr = deliveryReports(c);
            ArrayList<PendingIntent> sent = new ArrayList<PendingIntent>();
            ArrayList<PendingIntent> deliv = new ArrayList<PendingIntent>();
            for (int i = 0; i < parts.size(); i++) {
                Intent si = new Intent(ACTION_SENT).setClass(c, StatusReceiver.class).setData(u).putExtra("part", i).putExtra("parts", parts.size());
                sent.add(PendingIntent.getBroadcast(c, i, si, PendingIntent.FLAG_UPDATE_CURRENT));
                if (dr) {
                    Intent di = new Intent(ACTION_DELIVERED).setClass(c, StatusReceiver.class).setData(u).putExtra("part", i).putExtra("parts", parts.size());
                    deliv.add(PendingIntent.getBroadcast(c, 100 + i, di, PendingIntent.FLAG_UPDATE_CURRENT));
                }
            }
            if (parts.size() == 1) sm.sendTextMessage(address, null, body, sent.get(0), dr ? deliv.get(0) : null);
            else sm.sendMultipartTextMessage(address, null, parts, sent, dr ? deliv : null);
        } catch (RuntimeException e) {
            fail(c, u, -1);
        }
    }

    static void fail(Context c, Uri u, int code) {
        ContentValues v = new ContentValues();
        v.put("type", Telephony.Sms.MESSAGE_TYPE_FAILED);
        v.put("error_code", code);
        try { c.getContentResolver().update(u, v, null, null); } catch (RuntimeException e) { /* ignore */ }
    }

    // ----------------------------------------------------------------------------------------------- receiving

    static Uri insertIncoming(Context c, String address, String body, long date, long dateSent) {
        ContentValues v = new ContentValues();
        v.put("address", address);
        v.put("body", body);
        v.put("date", date);
        v.put("date_sent", dateSent);
        v.put("read", 0);
        v.put("seen", 0);
        v.put("type", Telephony.Sms.MESSAGE_TYPE_INBOX);
        return c.getContentResolver().insert(Telephony.Sms.Inbox.CONTENT_URI, v);
    }

    static int notifId(long threadId) { return 9000 + (int) (threadId % 100000); }

    static void ensureChannel(Context c) {
        NotificationChannel ch = new NotificationChannel(CH_MESSAGES, "Messages", NotificationManager.IMPORTANCE_HIGH);
        ch.enableVibration(true);
        ch.setLockscreenVisibility(Notification.VISIBILITY_PRIVATE);
        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).createNotificationChannel(ch);
    }

    static void notifyIncoming(Context c, long threadId, String address, String body) {
        if (!notifications(c)) return;
        ensureChannel(c);
        String who = KUi.nameOrNumber(c, address);
        Intent open = new Intent(c, ThreadActivity.class).putExtra("thread_id", threadId).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Intent reply = new Intent(c, ThreadActivity.class).putExtra("thread_id", threadId).putExtra("focus_compose", true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Intent mark = new Intent(ACTION_MARK_READ).setClass(c, StatusReceiver.class).putExtra("thread_id", threadId);
        Notification.Builder b = new Notification.Builder(c, CH_MESSAGES)
                .setSmallIcon(android.R.drawable.sym_action_email)
                .setContentTitle(who)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setCategory(Notification.CATEGORY_MESSAGE)
                .setAutoCancel(true)
                .setWhen(System.currentTimeMillis())
                .setContentIntent(PendingIntent.getActivity(c, (int) threadId, open, PendingIntent.FLAG_UPDATE_CURRENT))
                .addAction(new Notification.Action.Builder(null, "Reply",
                        PendingIntent.getActivity(c, (int) threadId + 1, reply, PendingIntent.FLAG_UPDATE_CURRENT)).build())
                .addAction(new Notification.Action.Builder(null, "Mark read",
                        PendingIntent.getBroadcast(c, (int) threadId, mark, PendingIntent.FLAG_UPDATE_CURRENT)).build());
        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).notify(notifId(threadId), b.build());
    }
}
