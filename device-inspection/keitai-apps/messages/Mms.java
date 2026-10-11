package org.kyf37.messages;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Telephony;
import android.telephony.SmsManager;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

/**
 * MMS basics without the hidden com.google.android.mms library: a small reader for m-notification-ind and
 * m-retrieve-conf PDUs (WSP encoded), a text-only m-send-req writer, and the provider rows the default SMS app owns.
 * Download and send go through the platform MmsService (SmsManager.downloadMultimediaMessage / sendMultimediaMessage).
 * Attachments other than text are stored but not displayed.
 */
final class Mms {
    private Mms() { }

    static final String ACTION_DOWNLOADED = "org.kyf37.messages.MMS_DOWNLOADED";
    static final String ACTION_SENT = "org.kyf37.messages.MMS_SENT";
    static final String AUTHORITY = "org.kyf37.messages.mms";

    static final class Part { String ct = ""; String name = ""; String cid = ""; String cl = ""; String charset = "UTF-8"; byte[] data = new byte[0]; }

    static final class Pdu {
        int type = -1; String transactionId = ""; String location = ""; String from = ""; String subject = "";
        long date; long size; String contentType = ""; ArrayList<String> to = new ArrayList<String>(); ArrayList<Part> parts = new ArrayList<Part>();
    }

    private static final String[] WELL_KNOWN = {
            "*/*", "text/*", "text/html", "text/plain", "text/x-hdml", "text/x-ttml", "text/x-vCalendar", "text/x-vCard",
            "text/vnd.wap.wml", "text/vnd.wap.wmlscript", "text/vnd.wap.wta-event", "multipart/*", "multipart/mixed",
            "multipart/form-data", "multipart/byteranges", "multipart/alternative", "application/*", "application/java-vm",
            "application/x-www-form-urlencoded", "application/x-hdmlc", "application/vnd.wap.wmlc", "application/vnd.wap.wmlscriptc",
            "application/vnd.wap.wta-eventc", "application/vnd.wap.uaprof", "application/vnd.wap.wtls-ca-certificate",
            "application/vnd.wap.wtls-user-certificate", "application/x-x509-ca-cert", "application/x-x509-user-cert",
            "image/*", "image/gif", "image/jpeg", "image/tiff", "image/png", "image/vnd.wap.wbmp", "application/vnd.wap.multipart.*",
            "application/vnd.wap.multipart.mixed", "application/vnd.wap.multipart.form-data", "application/vnd.wap.multipart.byteranges",
            "application/vnd.wap.multipart.alternative", "application/xml", "text/xml", "application/vnd.wap.wbxml",
            "application/x-x968-cross-cert-request", "application/x-x968-ca-cert", "application/x-x968-user-cert", "text/vnd.wap.si",
            "application/vnd.wap.sic", "text/vnd.wap.sl", "application/vnd.wap.slc", "text/vnd.wap.co", "application/vnd.wap.coc",
            "application/vnd.wap.multipart.related" };

    // ----------------------------------------------------------------------------------------------- reading

    private static final class Reader {
        final byte[] b; int p;
        Reader(byte[] b, int p) { this.b = b; this.p = p; }
        boolean more() { return p < b.length; }
        int peek() { return b[p] & 0xFF; }
        int u8() { return b[p++] & 0xFF; }
        long uintvar() {
            long v = 0;
            for (int i = 0; i < 5 && more(); i++) {
                int x = u8();
                v = (v << 7) | (x & 0x7F);
                if ((x & 0x80) == 0) break;
            }
            return v;
        }
        long valueLength() {
            int x = u8();
            if (x <= 30) return x;
            if (x == 31) return uintvar();
            p--;
            return -1;
        }
        String text() {
            if (more() && peek() == 0x7F) p++;
            int s = p;
            while (more() && b[p] != 0) p++;
            String r = new String(b, s, p - s, java.nio.charset.Charset.forName("UTF-8"));
            if (more()) p++;
            return r;
        }
        long longInt(int len) {
            long v = 0;
            for (int i = 0; i < len && more(); i++) v = (v << 8) | u8();
            return v;
        }
        /** Short-integer (0x80|n), Long-integer (len + bytes) or -1. */
        long anyInt() {
            int x = peek();
            if (x >= 0x80) { p++; return x & 0x7F; }
            if (x <= 30) { p++; return longInt(x); }
            return -1;
        }
        /** Encoded-string-value: plain text, or length + charset + text. */
        String encodedString() {
            int x = peek();
            if (x < 0x20) {
                int save = p;
                long len = valueLength();
                if (len < 0) { p = save; return text(); }
                int end = (int) Math.min(b.length, p + len);
                anyInt(); // charset
                String s = text();
                p = end;
                return s;
            }
            return text();
        }
    }

    /** Parses the MMS headers (everything up to and including Content-Type); the body offset is returned in bodyAt[0]. */
    static Pdu parse(byte[] pdu, int[] bodyAt) {
        Pdu o = new Pdu();
        Reader r = new Reader(pdu, 0);
        bodyAt[0] = pdu.length;
        try {
            while (r.more()) {
                int field = r.u8();
                switch (field) {
                    case 0x8C: o.type = r.u8(); break;                      // Message-Type
                    case 0x98: o.transactionId = r.text(); break;           // Transaction-Id
                    case 0x8D: r.u8(); break;                               // MMS-Version
                    case 0x83: o.location = r.text(); break;               // Content-Location
                    case 0x8E: o.size = r.anyInt(); break;                  // Message-Size
                    case 0x85: { int x = r.peek(); o.date = x <= 30 ? r.anyInt() : 0; if (x > 30) r.p++; break; } // Date
                    case 0x89: {                                            // From
                        long len = r.valueLength();
                        int end = (int) Math.min(pdu.length, r.p + len);
                        if (r.more() && r.peek() == 0x80) { r.p++; o.from = stripType(r.encodedString()); }
                        r.p = end;
                        break; }
                    case 0x97: o.to.add(stripType(r.encodedString())); break; // To
                    case 0x96: o.subject = r.encodedString(); break;        // Subject
                    case 0x84: {                                            // Content-Type: body follows
                        int x = r.peek();
                        if (x >= 0x80) { o.contentType = ct(x & 0x7F); r.p++; }
                        else if (x < 0x20) {
                            long len = r.valueLength();
                            int end = (int) Math.min(pdu.length, r.p + len);
                            int y = r.peek();
                            if (y >= 0x80) { o.contentType = ct(y & 0x7F); } else { o.contentType = r.text(); }
                            r.p = end;
                        } else { o.contentType = r.text(); }
                        bodyAt[0] = r.p;
                        return o; }
                    default: skipValue(r); break;
                }
            }
        } catch (RuntimeException e) {
            // truncated / unexpected PDU: return what we have
        }
        return o;
    }

    private static void skipValue(Reader r) {
        if (!r.more()) return;
        int x = r.peek();
        if (x >= 0x80) { r.p++; return; }
        if (x <= 30) { r.p++; r.p += x; return; }
        if (x == 31) { r.p++; long l = r.uintvar(); r.p += (int) l; return; }
        r.text();
    }

    private static String ct(int n) { return n < WELL_KNOWN.length ? WELL_KNOWN[n] : "application/octet-stream"; }

    private static String stripType(String a) {
        int i = a.indexOf("/TYPE=");
        return i > 0 ? a.substring(0, i) : a;
    }

    /** Parses a full m-retrieve-conf (headers + multipart body). */
    static Pdu parseRetrieveConf(byte[] pdu) {
        int[] at = new int[1];
        Pdu o = parse(pdu, at);
        if (at[0] >= pdu.length) return o;
        Reader r = new Reader(pdu, at[0]);
        try {
            long n = r.uintvar();
            for (long i = 0; i < n && r.more(); i++) {
                long hl = r.uintvar();
                long dl = r.uintvar();
                int hEnd = (int) Math.min(pdu.length, r.p + hl);
                Part part = new Part();
                // content type
                int x = r.peek();
                if (x >= 0x80) { part.ct = ct(x & 0x7F); r.p++; }
                else if (x < 0x20) {
                    long len = r.valueLength();
                    int end = (int) Math.min(hEnd, r.p + len);
                    int y = r.peek();
                    if (y >= 0x80) { part.ct = ct(y & 0x7F); r.p++; } else { part.ct = r.text(); }
                    while (r.p < end) {
                        int prm = r.u8();
                        if (prm == 0x81) { long cs = r.anyInt(); part.charset = charset((int) cs); }              // Charset
                        else if (prm == 0x85 || prm == 0x97) { part.name = r.text(); }                        // Name / Filename
                        else { skipValue(r); }
                    }
                    r.p = end;
                } else { part.ct = r.text(); }
                while (r.p < hEnd) {
                    int h = r.u8();
                    if (h == 0x8E) part.cl = r.text();                                                       // Content-Location
                    else if (h == 0xC0) part.cid = r.text();                                                 // Content-ID
                    else skipValue(r);
                }
                r.p = hEnd;
                int dEnd = (int) Math.min(pdu.length, r.p + dl);
                part.data = java.util.Arrays.copyOfRange(pdu, r.p, dEnd);
                r.p = dEnd;
                o.parts.add(part);
            }
        } catch (RuntimeException e) {
            // keep the parts parsed so far
        }
        return o;
    }

    private static String charset(int mib) {
        switch (mib) {
            case 3: return "US-ASCII";
            case 4: return "ISO-8859-1";
            case 106: return "UTF-8";
            case 1013: return "UTF-16BE";
            case 1015: return "UTF-16";
            default: return "UTF-8";
        }
    }

    // ----------------------------------------------------------------------------------------------- writing

    /** Minimal text-only m-send-req. Recipients are PLMN numbers. */
    static byte[] buildSendReq(Iterable<String> to, String text) throws IOException {
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        o.write(0x8C); o.write(0x80);                                   // m-send-req
        o.write(0x98); str(o, "T" + Long.toHexString(System.nanoTime()));
        o.write(0x8D); o.write(0x92);                                   // 1.2
        o.write(0x89); o.write(0x01); o.write(0x81);                    // From: insert-address
        for (String t : to) { o.write(0x97); str(o, t + "/TYPE=PLMN"); }
        o.write(0x84); o.write(0xA3);                                   // multipart/mixed
        byte[] data = text.getBytes("UTF-8");
        ByteArrayOutputStream h = new ByteArrayOutputStream();
        h.write(0x03); h.write(0x83); h.write(0x81); h.write(0xEA);     // text/plain; charset=utf-8
        h.write(0x8E); str(h, "text_0.txt");                            // Content-Location
        o.write(0x01);                                                  // one entry
        uintvar(o, h.size());
        uintvar(o, data.length);
        o.write(h.toByteArray());
        o.write(data);
        return o.toByteArray();
    }

    private static void str(OutputStream o, String s) throws IOException { o.write(s.getBytes("UTF-8")); o.write(0); }

    private static void uintvar(OutputStream o, long v) throws IOException {
        byte[] tmp = new byte[5];
        int n = 0;
        tmp[n++] = (byte) (v & 0x7F);
        v >>= 7;
        while (v > 0) { tmp[n++] = (byte) (0x80 | (v & 0x7F)); v >>= 7; }
        while (n > 0) o.write(tmp[--n]);
    }

    // ----------------------------------------------------------------------------------------------- storage

    static File dir(Context c) {
        File d = new File(c.getCacheDir(), "mms");
        d.mkdirs();
        return d;
    }

    static Uri fileUri(String name) { return new Uri.Builder().scheme("content").authority(AUTHORITY).path("/" + name).build(); }

    private static int addrType(boolean from) { return from ? 137 : 151; }

    private static void addAddr(ContentResolver cr, long msgId, String addr, int type) {
        ContentValues v = new ContentValues();
        v.put("address", addr);
        v.put("type", type);
        v.put("charset", 106);
        cr.insert(Uri.parse("content://mms/" + msgId + "/addr"), v);
    }

    private static void addPart(ContentResolver cr, long msgId, Part p) {
        ContentValues v = new ContentValues();
        v.put("mid", msgId);
        v.put("ct", p.ct);
        v.put("chset", 106);
        if (p.name.length() > 0) v.put("name", p.name);
        if (p.cl.length() > 0) v.put("cl", p.cl);
        if (p.cid.length() > 0) v.put("cid", p.cid);
        boolean text = p.ct.startsWith("text/plain");
        if (text) {
            try { v.put("text", new String(p.data, p.charset)); } catch (IOException e) { v.put("text", new String(p.data)); }
        }
        Uri u = cr.insert(Uri.parse("content://mms/" + msgId + "/part"), v);
        if (u != null && !text && p.data.length > 0) {
            try {
                OutputStream os = cr.openOutputStream(u);
                if (os != null) { try { os.write(p.data); } finally { os.close(); } }
            } catch (IOException e) {
                // part metadata is kept, data missing
            }
        }
    }

    /** Inserts a retrieved message into the inbox. Returns the thread id (or -1). */
    static long storeInbox(Context c, Pdu m, long notifRow) {
        ContentResolver cr = c.getContentResolver();
        long thread = m.from.length() > 0 ? Telephony.Threads.getOrCreateThreadId(c, m.from) : 0;
        if (notifRow > 0) { try { cr.delete(ContentUris.withAppendedId(Telephony.Mms.CONTENT_URI, notifRow), null, null); } catch (RuntimeException e) { /* ignore */ } }
        ContentValues v = new ContentValues();
        v.put("thread_id", thread);
        v.put("date", m.date > 0 ? m.date : System.currentTimeMillis() / 1000);
        v.put("msg_box", 1);
        v.put("read", 0);
        v.put("seen", 0);
        v.put("sub", m.subject);
        v.put("sub_cs", 106);
        v.put("ct_t", "application/vnd.wap.multipart.related");
        v.put("m_type", 132);
        v.put("v", 18);
        v.put("m_size", m.size);
        v.put("tr_id", m.transactionId);
        v.put("pri", 129);
        Uri u = cr.insert(Telephony.Mms.CONTENT_URI, v);
        if (u == null) return -1;
        long id = ContentUris.parseId(u);
        addAddr(cr, id, m.from.length() > 0 ? m.from : "insert-address-token", 137);
        for (Part p : m.parts) addPart(cr, id, p);
        return thread;
    }

    /** Stores the "you have an MMS waiting" row so the user sees it even if the download fails. */
    static long storeNotification(Context c, Pdu n) {
        ContentResolver cr = c.getContentResolver();
        long thread = n.from.length() > 0 ? Telephony.Threads.getOrCreateThreadId(c, n.from) : 0;
        ContentValues v = new ContentValues();
        v.put("thread_id", thread);
        v.put("date", System.currentTimeMillis() / 1000);
        v.put("msg_box", 1);
        v.put("read", 0);
        v.put("seen", 0);
        v.put("sub", n.subject);
        v.put("sub_cs", 106);
        v.put("ct_l", n.location);
        v.put("m_type", 130);
        v.put("v", 18);
        v.put("m_size", n.size);
        v.put("tr_id", n.transactionId);
        v.put("pri", 129);
        Uri u = cr.insert(Telephony.Mms.CONTENT_URI, v);
        if (u == null) return -1;
        long id = ContentUris.parseId(u);
        if (n.from.length() > 0) addAddr(cr, id, n.from, 137);
        return id;
    }

    /** Starts the platform download. The result arrives at {@link MmsReceiver.Status}. */
    static void download(Context c, Pdu n, long notifRow) {
        String name = "dl_" + System.currentTimeMillis() + ".pdu";
        File f = new File(dir(c), name);
        try { f.createNewFile(); } catch (IOException e) { return; }
        Intent i = new Intent(ACTION_DOWNLOADED).setClass(c, MmsReceiver.Status.class)
                .putExtra("file", name).putExtra("notif_row", notifRow).putExtra("from", n.from).putExtra("subject", n.subject)
                .putExtra("tr_id", n.transactionId);
        PendingIntent pi = PendingIntent.getBroadcast(c, (int) (System.currentTimeMillis() & 0xFFFFFF), i, PendingIntent.FLAG_ONE_SHOT);
        try {
            SmsManager.getDefault().downloadMultimediaMessage(c, n.location, fileUri(name), new Bundle(), pi);
        } catch (RuntimeException e) {
            // no radio / no permission: the notification row remains and can be retried from the thread menu
        }
    }

    /** Text-only MMS send: writes the PDU, an outbox row, and asks MmsService to send it. */
    static void sendText(Context c, ArrayList<String> to, String text) throws IOException {
        ContentResolver cr = c.getContentResolver();
        long thread = to.size() == 1 ? Telephony.Threads.getOrCreateThreadId(c, to.get(0))
                : Telephony.Threads.getOrCreateThreadId(c, new HashSet<String>(to));
        ContentValues v = new ContentValues();
        v.put("thread_id", thread);
        v.put("date", System.currentTimeMillis() / 1000);
        v.put("msg_box", 4);
        v.put("read", 1);
        v.put("seen", 1);
        v.put("ct_t", "application/vnd.wap.multipart.mixed");
        v.put("m_type", 128);
        v.put("v", 18);
        v.put("pri", 129);
        Uri u = cr.insert(Telephony.Mms.CONTENT_URI, v);
        if (u == null) throw new IOException("provider refused the message");
        long id = ContentUris.parseId(u);
        for (String t : to) addAddr(cr, id, t, 151);
        addAddr(cr, id, "insert-address-token", 137);
        Part p = new Part();
        p.ct = "text/plain"; p.name = "text_0.txt"; p.cl = "text_0.txt"; p.data = text.getBytes("UTF-8");
        addPart(cr, id, p);
        String name = "send_" + id + ".pdu";
        FileOutputStream os = new FileOutputStream(new File(dir(c), name));
        try { os.write(buildSendReq(to, text)); } finally { os.close(); }
        Intent i = new Intent(ACTION_SENT).setClass(c, MmsReceiver.Status.class).putExtra("row", id).putExtra("file", name);
        PendingIntent pi = PendingIntent.getBroadcast(c, (int) id, i, PendingIntent.FLAG_UPDATE_CURRENT);
        try {
            SmsManager.getDefault().sendMultimediaMessage(c, fileUri(name), null, new Bundle(), pi);
        } catch (RuntimeException e) {
            ContentValues f = new ContentValues();
            f.put("msg_box", 5);
            cr.update(ContentUris.withAppendedId(Telephony.Mms.CONTENT_URI, id), f, null, null);
        }
    }

    static byte[] readFile(File f) throws IOException {
        FileInputStream in = new FileInputStream(f);
        try {
            ByteArrayOutputStream o = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) o.write(buf, 0, n);
            return o.toByteArray();
        } finally {
            in.close();
        }
    }

    static boolean ok(int resultCode) { return resultCode == Activity.RESULT_OK; }
}
