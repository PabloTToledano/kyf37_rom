package org.kyf37.contacts;

import java.io.File;
import java.io.FileOutputStream;
import java.util.List;

/** Host JVM test of the vCard reader/writer. */
public final class VCardHostTest {
    static int fails;
    static void check(boolean ok, String what) {
        if (!ok) { fails++; System.out.println("FAIL " + what); } else { System.out.println("ok   " + what); }
    }

    static List<Store.Card> parse(String text) throws Exception {
        File f = File.createTempFile("vcard", ".vcf");
        FileOutputStream o = new FileOutputStream(f);
        o.write(text.getBytes("UTF-8"));
        o.close();
        try { return VCard.parse(f); } finally { f.delete(); }
    }

    public static void main(String[] a) throws Exception {
        List<Store.Card> v3 = parse("BEGIN:VCARD\r\nVERSION:3.0\r\nN:Adams;Alice;;;\r\nFN:Alice Adams\r\nTEL;TYPE=CELL:+34 600 111 222\r\nTEL;TYPE=HOME,VOICE:910000000\r\n"
                + "EMAIL;TYPE=INTERNET:alice@example.com\r\nNOTE:line one\\nline two\\, with comma\r\nORG:ACME\\;Inc;Dept\r\nEND:VCARD\r\n"
                + "BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Bob\r\n TheBuilder\r\nTEL;TYPE=WORK:915555555\r\nTEL:600333444\r\nEND:VCARD\r\n");
        check(v3.size() == 2, "v3 count " + v3.size());
        Store.Card x = v3.get(0);
        check(x.name.equals("Alice Adams"), "name " + x.name);
        check(x.mobile.equals("+34 600 111 222"), "mobile " + x.mobile);
        check(x.home.equals("910000000"), "home " + x.home);
        check(x.email.equals("alice@example.com"), "email");
        check(x.note.equals("line one\nline two, with comma"), "note unescape " + x.note);
        check(x.org.startsWith("ACME"), "org " + x.org);
        Store.Card y = v3.get(1);
        check(y.name.equals("BobTheBuilder"), "folded name " + y.name);
        check(y.work.equals("915555555"), "work");
        check(y.mobile.equals("600333444"), "untyped tel goes to mobile");

        List<Store.Card> v21 = parse("BEGIN:VCARD\r\nVERSION:2.1\r\nN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:=4A=C3=B6rg;=48ans;;;\r\n"
                + "TEL;CELL:600777888\r\nNOTE;ENCODING=QUOTED-PRINTABLE:abc=\r\ndef\r\nEND:VCARD\r\n");
        check(v21.size() == 1, "v21 count");
        check(v21.size() == 1 && v21.get(0).name.equals("Hans Jörg"), "v21 qp name " + (v21.size() == 1 ? v21.get(0).name : ""));
        check(v21.size() == 1 && v21.get(0).mobile.equals("600777888"), "v21 cell");
        check(v21.size() == 1 && v21.get(0).note.equals("abcdef"), "v21 qp soft break " + (v21.size() == 1 ? v21.get(0).note : ""));

        Store.Card k = new Store.Card();
        k.name = "Zoë Quinn"; k.mobile = "600000001"; k.home = "910000002"; k.work = "910000003"; k.email = "z@q.org"; k.note = "a;b,c\nd";
        List<Store.Card> rt = parse(VCard.write(java.util.Collections.singletonList(k)));
        check(rt.size() == 1, "roundtrip count");
        if (rt.size() == 1) {
            Store.Card r = rt.get(0);
            check(r.name.equals(k.name) && r.mobile.equals(k.mobile) && r.home.equals(k.home) && r.work.equals(k.work) && r.email.equals(k.email) && r.note.equals(k.note), "roundtrip fields");
        }
        check(parse("garbage\r\nBEGIN:VCARD\r\nEND:VCARD\r\n").isEmpty(), "empty card dropped");
        System.out.println(fails == 0 ? "ALL PASS" : fails + " FAILED");
        System.exit(fails == 0 ? 0 : 1);
    }
}
