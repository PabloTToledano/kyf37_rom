package org.kyf37.contacts;

import android.content.Context;
import android.provider.ContactsContract.CommonDataKinds.Phone;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * Minimal vCard 2.1 / 3.0 / 4.0 reader and 3.0 writer for the fields the edit screen knows
 * (name, three phone slots + extras, e-mail, note, organisation). No photos, no addresses.
 */
final class VCard {
    private VCard() { }

    // --------------------------------------------------------------------------------------------- reading

    static List<Store.Card> parse(File f) throws IOException {
        BufferedReader r = new BufferedReader(new InputStreamReader(new FileInputStream(f), "UTF-8"));
        ArrayList<String> lines = new ArrayList<String>();
        try {
            String line;
            String prev = null;
            while ((line = r.readLine()) != null) {
                if (line.length() > 0 && (line.charAt(0) == ' ' || line.charAt(0) == '\t') && prev != null) {
                    prev = prev + line.substring(1); // folded line
                    lines.set(lines.size() - 1, prev);
                    continue;
                }
                // quoted-printable soft line break: value continues on the next line
                if (prev != null && prev.endsWith("=") && prev.toUpperCase().contains("QUOTED-PRINTABLE")) {
                    prev = prev.substring(0, prev.length() - 1) + line;
                    lines.set(lines.size() - 1, prev);
                    continue;
                }
                prev = line;
                lines.add(line);
            }
        } finally {
            r.close();
        }
        ArrayList<Store.Card> out = new ArrayList<Store.Card>();
        Store.Card cur = null;
        String fn = null, structured = null;
        for (String raw : lines) {
            String line = raw.trim();
            if (line.length() == 0) continue;
            String up = line.toUpperCase();
            if (up.equals("BEGIN:VCARD")) { cur = new Store.Card(); fn = null; structured = null; continue; }
            if (up.equals("END:VCARD")) {
                if (cur != null) {
                    cur.name = fn != null && fn.length() > 0 ? fn : (structured == null ? "" : structured);
                    if (!cur.isEmpty()) out.add(cur);
                }
                cur = null;
                continue;
            }
            if (cur == null) continue;
            int colon = line.indexOf(':');
            if (colon < 0) continue;
            String head = line.substring(0, colon);
            String value = line.substring(colon + 1);
            String[] parts = head.split(";");
            String prop = parts[0].toUpperCase();
            int dot = prop.lastIndexOf('.'); // group prefix item1.TEL
            if (dot >= 0) prop = prop.substring(dot + 1);
            String charset = "UTF-8";
            boolean qp = false;
            StringBuilder types = new StringBuilder();
            for (int i = 1; i < parts.length; i++) {
                String p = parts[i].toUpperCase();
                if (p.startsWith("CHARSET=")) charset = parts[i].substring(8);
                else if (p.startsWith("ENCODING=")) qp = p.endsWith("QUOTED-PRINTABLE");
                else if (p.equals("QUOTED-PRINTABLE")) qp = true;
                else if (p.startsWith("TYPE=")) types.append(p.substring(5)).append(',');
                else types.append(p).append(',');
            }
            if (qp) value = decodeQp(value, charset);
            String t = types.toString();
            if (prop.equals("FN")) fn = unescape(value);
            else if (prop.equals("N")) structured = structuredName(value);
            else if (prop.equals("TEL")) {
                String num = unescape(value).replace("tel:", "").trim();
                if (num.length() == 0) continue;
                if (t.contains("CELL") && cur.mobile.length() == 0) cur.mobile = num;
                else if (t.contains("HOME") && cur.home.length() == 0) cur.home = num;
                else if (t.contains("WORK") && cur.work.length() == 0) cur.work = num;
                else if (cur.mobile.length() == 0) cur.mobile = num;
                else cur.otherPhones.add(new String[] { num, String.valueOf(Phone.TYPE_OTHER) });
            } else if (prop.equals("EMAIL")) { if (cur.email.length() == 0) cur.email = unescape(value).trim(); }
            else if (prop.equals("NOTE")) { if (cur.note.length() == 0) cur.note = unescape(value); }
            else if (prop.equals("ORG")) { if (cur.org.length() == 0) cur.org = unescape(value).replace(';', ' ').trim(); }
        }
        return out;
    }

    private static String structuredName(String v) {
        String[] p = v.split(";", -1); // family;given;additional;prefix;suffix
        StringBuilder b = new StringBuilder();
        if (p.length > 3 && p[3].length() > 0) b.append(p[3]).append(' ');
        if (p.length > 1 && p[1].length() > 0) b.append(p[1]).append(' ');
        if (p.length > 2 && p[2].length() > 0) b.append(p[2]).append(' ');
        if (p.length > 0 && p[0].length() > 0) b.append(p[0]).append(' ');
        if (p.length > 4 && p[4].length() > 0) b.append(p[4]);
        return unescape(b.toString().trim());
    }

    private static String decodeQp(String s, String charset) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '=' && i + 2 < s.length() + 0 && isHex(s.charAt(i + 1)) && isHex(s.charAt(i + 2))) {
                out.write(Integer.parseInt(s.substring(i + 1, i + 3), 16));
                i += 2;
            } else if (ch < 128) {
                out.write(ch);
            } else {
                try { byte[] b = String.valueOf(ch).getBytes("UTF-8"); out.write(b, 0, b.length); } catch (IOException e) { out.write('?'); }
            }
        }
        try { return out.toString(charset); } catch (IOException e) { return out.toString(); }
    }

    private static boolean isHex(char c) { return Character.digit(c, 16) >= 0; }

    private static String unescape(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\' && i + 1 < s.length()) {
                char n = s.charAt(++i);
                b.append(n == 'n' || n == 'N' ? '\n' : n);
            } else {
                b.append(c);
            }
        }
        return b.toString();
    }

    // --------------------------------------------------------------------------------------------- writing

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n");
    }

    static String write(List<Store.Card> cards) {
        StringBuilder b = new StringBuilder();
        for (Store.Card k : cards) {
            b.append("BEGIN:VCARD\r\nVERSION:3.0\r\n");
            String name = k.name.length() == 0 ? (k.mobile.length() > 0 ? k.mobile : "?") : k.name;
            String[] sp = name.split(" ", 2);
            b.append("N:").append(sp.length > 1 ? esc(sp[1]) : "").append(';').append(esc(sp[0])).append(";;;\r\n");
            b.append("FN:").append(esc(name)).append("\r\n");
            if (k.mobile.length() > 0) b.append("TEL;TYPE=CELL:").append(esc(k.mobile)).append("\r\n");
            if (k.home.length() > 0) b.append("TEL;TYPE=HOME:").append(esc(k.home)).append("\r\n");
            if (k.work.length() > 0) b.append("TEL;TYPE=WORK:").append(esc(k.work)).append("\r\n");
            for (String[] p : k.otherPhones) b.append("TEL;TYPE=VOICE:").append(esc(p[0])).append("\r\n");
            if (k.email.length() > 0) b.append("EMAIL;TYPE=INTERNET:").append(esc(k.email)).append("\r\n");
            if (k.org.length() > 0) b.append("ORG:").append(esc(k.org)).append("\r\n");
            if (k.note.length() > 0) b.append("NOTE:").append(esc(k.note)).append("\r\n");
            b.append("END:VCARD\r\n");
        }
        return b.toString();
    }

    /** Where exports go and where imports look first: SD card if present, else shared storage. */
    static ArrayList<File> roots(Context ctx) {
        ArrayList<File> roots = new ArrayList<File>();
        File[] storage = new File("/storage").listFiles();
        if (storage != null) {
            for (File f : storage) {
                String n = f.getName();
                if (n.equals("self") || n.equals("emulated")) continue;
                if (f.isDirectory() && f.canRead()) roots.add(f);
            }
        }
        File ext = android.os.Environment.getExternalStorageDirectory();
        if (ext != null && ext.isDirectory()) roots.add(ext);
        return roots;
    }
}
