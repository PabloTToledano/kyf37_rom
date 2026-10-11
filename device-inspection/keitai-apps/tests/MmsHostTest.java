package org.kyf37.messages;

import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Arrays;

/** Host JVM test of the WSP/MMS PDU reader and writer (no Android runtime needed). */
public final class MmsHostTest {
    static int fails;

    static void check(boolean ok, String what) {
        if (!ok) { fails++; System.out.println("FAIL " + what); } else { System.out.println("ok   " + what); }
    }

    static void str(ByteArrayOutputStream o, String s) throws Exception { o.write(s.getBytes("UTF-8")); o.write(0); }

    public static void main(String[] a) throws Exception {
        // 1. our own text-only m-send-req parses back
        ArrayList<String> to = new ArrayList<String>();
        to.add("+34600123456");
        byte[] req = Mms.buildSendReq(to, "Hello áñ world");
        int[] at = new int[1];
        Mms.Pdu p = Mms.parse(req, at);
        check(p.type == 0x80, "send-req type");
        check(p.to.size() == 1 && p.to.get(0).equals("+34600123456"), "send-req recipient " + p.to);
        check(p.contentType.equals("application/vnd.wap.multipart.mixed"), "send-req content type " + p.contentType);
        Mms.Pdu body = Mms.parseRetrieveConf(req);
        check(body.parts.size() == 1, "send-req one part");
        check(body.parts.size() == 1 && body.parts.get(0).ct.equals("text/plain") && new String(body.parts.get(0).data, "UTF-8").equals("Hello áñ world"), "send-req text round trip");
        check(body.parts.size() == 1 && body.parts.get(0).charset.equals("UTF-8"), "send-req charset utf-8");
        check(body.parts.size() == 1 && body.parts.get(0).cl.equals("text_0.txt"), "send-req content-location");

        // 2. hand built m-notification-ind
        ByteArrayOutputStream n = new ByteArrayOutputStream();
        n.write(0x8C); n.write(0x82);
        n.write(0x98); str(n, "TID42");
        n.write(0x8D); n.write(0x92);
        n.write(0x89);
        ByteArrayOutputStream from = new ByteArrayOutputStream();
        from.write(0x80); str(from, "+34611222333/TYPE=PLMN");
        n.write(from.size()); n.write(from.toByteArray());
        n.write(0x8A); n.write(0x80);
        n.write(0x96); str(n, "Holiday");
        n.write(0x8E); n.write(0x02); n.write(0x13); n.write(0x88); // size 5000
        n.write(0x88); n.write(0x05); n.write(0x81); n.write(0x03); n.write(0x00); n.write(0x00); n.write(0x00); // expiry relative
        n.write(0x83); str(n, "http://mms.example.net/get?id=1");
        Mms.Pdu ni = Mms.parse(n.toByteArray(), at);
        check(ni.type == 0x82, "notification type");
        check(ni.transactionId.equals("TID42"), "notification tid " + ni.transactionId);
        check(ni.from.equals("+34611222333"), "notification from " + ni.from);
        check(ni.subject.equals("Holiday"), "notification subject " + ni.subject);
        check(ni.size == 5000, "notification size " + ni.size);
        check(ni.location.equals("http://mms.example.net/get?id=1"), "notification location " + ni.location);

        // 3. hand built m-retrieve-conf, multipart.related with SMIL, text and a jpeg
        ByteArrayOutputStream r = new ByteArrayOutputStream();
        r.write(0x8C); r.write(0x84);
        r.write(0x98); str(r, "TID43");
        r.write(0x8D); r.write(0x92);
        r.write(0x85); r.write(0x04); r.write(0x5F); r.write(0x00); r.write(0x00); r.write(0x01); // date
        r.write(0x89); r.write(from.size()); r.write(from.toByteArray());
        r.write(0x96); str(r, "Pic");
        r.write(0x84); r.write(0xB3); // application/vnd.wap.multipart.related
        r.write(0x03); // three entries
        byte[] smil = "<smil/>".getBytes("UTF-8");
        byte[] txt = "café time".getBytes("UTF-8");
        byte[] jpg = new byte[300];
        Arrays.fill(jpg, (byte) 0xAB);
        ByteArrayOutputStream h1 = new ByteArrayOutputStream();
        str(h1, "application/smil"); h1.write(0x8E); str(h1, "smil.xml");
        entry(r, h1.toByteArray(), smil);
        ByteArrayOutputStream h2 = new ByteArrayOutputStream();
        h2.write(0x03); h2.write(0x83); h2.write(0x81); h2.write(0xEA); h2.write(0x8E); str(h2, "t.txt");
        entry(r, h2.toByteArray(), txt);
        ByteArrayOutputStream h3 = new ByteArrayOutputStream();
        ByteArrayOutputStream ctv = new ByteArrayOutputStream();
        ctv.write(0x9E); ctv.write(0x85); str(ctv, "a.jpg");
        h3.write(ctv.size()); h3.write(ctv.toByteArray());
        h3.write(0xC0); str(h3, "<img1>");
        entry(r, h3.toByteArray(), jpg);
        Mms.Pdu rc = Mms.parseRetrieveConf(r.toByteArray());
        check(rc.type == 0x84, "retrieve type");
        check(rc.contentType.equals("application/vnd.wap.multipart.related"), "retrieve content type " + rc.contentType);
        check(rc.date == 0x5F000001L, "retrieve date " + rc.date);
        check(rc.subject.equals("Pic"), "retrieve subject");
        check(rc.parts.size() == 3, "retrieve 3 parts, got " + rc.parts.size());
        if (rc.parts.size() == 3) {
            check(rc.parts.get(0).ct.equals("application/smil") && rc.parts.get(0).cl.equals("smil.xml"), "part1 smil");
            check(rc.parts.get(1).ct.equals("text/plain") && new String(rc.parts.get(1).data, "UTF-8").equals("café time"), "part2 text");
            check(rc.parts.get(2).ct.equals("image/jpeg") && rc.parts.get(2).name.equals("a.jpg") && rc.parts.get(2).cid.equals("<img1>") && rc.parts.get(2).data.length == 300,
                    "part3 jpeg " + rc.parts.get(2).ct + " " + rc.parts.get(2).name + " " + rc.parts.get(2).cid);
        }
        // 4. garbage must not throw
        Mms.Pdu g = Mms.parse(new byte[] { (byte) 0x8C, 0x12, 0x34, (byte) 0xFF }, at);
        check(g != null, "garbage tolerated");
        Mms.Pdu g2 = Mms.parseRetrieveConf(new byte[0]);
        check(g2.parts.isEmpty(), "empty tolerated");
        System.out.println(fails == 0 ? "ALL PASS" : fails + " FAILED");
        System.exit(fails == 0 ? 0 : 1);
    }

    static void uv(ByteArrayOutputStream o, int v) {
        if (v < 128) { o.write(v); return; }
        o.write(0x80 | (v >> 7)); o.write(v & 0x7F);
    }

    static void entry(ByteArrayOutputStream o, byte[] headers, byte[] data) throws Exception {
        uv(o, headers.length); uv(o, data.length); o.write(headers); o.write(data);
    }
}
