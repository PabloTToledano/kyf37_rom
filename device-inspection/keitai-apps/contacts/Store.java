package org.kyf37.contacts;

import android.content.ContentProviderOperation;
import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.ContactsContract;
import android.provider.ContactsContract.CommonDataKinds.Email;
import android.provider.ContactsContract.CommonDataKinds.Note;
import android.provider.ContactsContract.CommonDataKinds.Organization;
import android.provider.ContactsContract.CommonDataKinds.Phone;
import android.provider.ContactsContract.CommonDataKinds.StructuredName;
import android.provider.ContactsContract.Contacts;
import android.provider.ContactsContract.Data;
import android.provider.ContactsContract.RawContacts;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;

/** ContactsContract access for the Contacts app. All calls may throw SecurityException if permissions were revoked. */
final class Store {
    private Store() { }

    static final class C {
        long id; String lookup; String name; boolean starred; String number;
        Uri uri() { return Contacts.getLookupUri(id, lookup); }
    }

    static final class Datum {
        long id; String mime; String v1; String v2; int type; String label;
    }

    /** Editable view of one contact; used by the edit screen and the vCard importer. */
    static final class Card {
        String name = "", mobile = "", home = "", work = "", email = "", note = "", org = "";
        ArrayList<String[]> otherPhones = new ArrayList<String[]>(); // {number, type}
        boolean isEmpty() { return name.length() == 0 && mobile.length() == 0 && home.length() == 0 && work.length() == 0 && email.length() == 0 && note.length() == 0; }
    }

    static ArrayList<C> load(Context ctx, String filter, boolean starredOnly) {
        ContentResolver cr = ctx.getContentResolver();
        ArrayList<C> out = new ArrayList<C>();
        StringBuilder sel = new StringBuilder(Contacts.DISPLAY_NAME + " IS NOT NULL");
        ArrayList<String> args = new ArrayList<String>();
        if (starredOnly) sel.append(" AND ").append(Contacts.STARRED).append("=1");
        if (filter != null && filter.length() > 0) {
            HashSet<Long> byNumber = new HashSet<Long>();
            Cursor pc = null;
            try {
                pc = cr.query(Phone.CONTENT_URI, new String[] { Phone.CONTACT_ID }, Phone.NUMBER + " LIKE ?", new String[] { "%" + filter + "%" }, null);
                while (pc != null && pc.moveToNext()) byNumber.add(pc.getLong(0));
            } catch (RuntimeException e) {
                // fall back to name only
            } finally {
                if (pc != null) pc.close();
            }
            sel.append(" AND (").append(Contacts.DISPLAY_NAME).append(" LIKE ?");
            args.add("%" + filter + "%");
            if (!byNumber.isEmpty()) {
                sel.append(" OR ").append(Contacts._ID).append(" IN (");
                boolean first = true;
                for (Long l : byNumber) { if (!first) sel.append(','); sel.append(l.longValue()); first = false; }
                sel.append(")");
            }
            sel.append(")");
        }
        Cursor c = null;
        try {
            c = cr.query(Contacts.CONTENT_URI, new String[] { Contacts._ID, Contacts.LOOKUP_KEY, Contacts.DISPLAY_NAME, Contacts.STARRED },
                    sel.toString(), args.toArray(new String[0]), Contacts.SORT_KEY_PRIMARY + " COLLATE LOCALIZED ASC");
            while (c != null && c.moveToNext()) {
                C x = new C();
                x.id = c.getLong(0); x.lookup = c.getString(1); x.name = c.getString(2); x.starred = c.getInt(3) != 0;
                out.add(x);
            }
        } finally {
            if (c != null) c.close();
        }
        HashMap<Long, String> nums = primaryNumbers(ctx);
        for (C x : out) x.number = nums.get(x.id);
        return out;
    }

    static HashMap<Long, String> primaryNumbers(Context ctx) {
        HashMap<Long, String> m = new HashMap<Long, String>();
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(Phone.CONTENT_URI, new String[] { Phone.CONTACT_ID, Phone.NUMBER },
                    null, null, Phone.CONTACT_ID + ", " + Phone.IS_SUPER_PRIMARY + " DESC, " + Phone.IS_PRIMARY + " DESC, " + Phone._ID);
            while (c != null && c.moveToNext()) {
                long id = c.getLong(0);
                if (!m.containsKey(id)) m.put(id, c.getString(1));
            }
        } catch (RuntimeException e) {
            // empty
        } finally {
            if (c != null) c.close();
        }
        return m;
    }

    /** Accepts contact, lookup and legacy people URIs. Returns -1 when the contact does not exist. */
    static long contactId(Context ctx, Uri u) {
        if (u == null) return -1;
        try {
            String s = u.toString();
            if (s.startsWith("content://contacts/people/")) {
                return ContentUris.parseId(u);
            }
            java.util.List<String> seg = u.getPathSegments();
            if (seg.size() == 2 && "contacts".equals(seg.get(0)) && seg.get(1).matches("[0-9]+")) {
                return Long.parseLong(seg.get(1));
            }
            Uri res = Contacts.lookupContact(ctx.getContentResolver(), u);
            if (res != null) return ContentUris.parseId(res);
        } catch (RuntimeException e) {
            return -1;
        }
        return -1;
    }

    static String name(Context ctx, long contactId) {
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(ContentUris.withAppendedId(Contacts.CONTENT_URI, contactId), new String[] { Contacts.DISPLAY_NAME }, null, null, null);
            if (c != null && c.moveToFirst()) return c.getString(0);
        } finally {
            if (c != null) c.close();
        }
        return null;
    }

    static boolean starred(Context ctx, long contactId) {
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(ContentUris.withAppendedId(Contacts.CONTENT_URI, contactId), new String[] { Contacts.STARRED }, null, null, null);
            return c != null && c.moveToFirst() && c.getInt(0) != 0;
        } finally {
            if (c != null) c.close();
        }
    }

    static void setStarred(Context ctx, long contactId, boolean on) {
        ContentValues v = new ContentValues();
        v.put(Contacts.STARRED, on ? 1 : 0);
        ctx.getContentResolver().update(ContentUris.withAppendedId(Contacts.CONTENT_URI, contactId), v, null, null);
    }

    static boolean delete(Context ctx, long contactId) {
        Uri u = ContentUris.withAppendedId(Contacts.CONTENT_URI, contactId);
        return ctx.getContentResolver().delete(u, null, null) > 0;
    }

    static ArrayList<Datum> data(Context ctx, long contactId) {
        ArrayList<Datum> out = new ArrayList<Datum>();
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(Data.CONTENT_URI,
                    new String[] { Data._ID, Data.MIMETYPE, Data.DATA1, Data.DATA2, Data.DATA3 },
                    Data.CONTACT_ID + "=?", new String[] { String.valueOf(contactId) }, Data.IS_SUPER_PRIMARY + " DESC, " + Data.IS_PRIMARY + " DESC, " + Data._ID);
            while (c != null && c.moveToNext()) {
                Datum d = new Datum();
                d.id = c.getLong(0); d.mime = c.getString(1); d.v1 = c.getString(2);
                d.type = c.getInt(3); d.v2 = c.getString(3); d.label = c.getString(4);
                out.add(d);
            }
        } finally {
            if (c != null) c.close();
        }
        return out;
    }

    static String typeLabel(Context ctx, int mime, int type, String label) {
        CharSequence cs = mime == 0 ? Phone.getTypeLabel(ctx.getResources(), type, label) : Email.getTypeLabel(ctx.getResources(), type, label);
        return String.valueOf(cs);
    }

    static long rawContactId(Context ctx, long contactId) {
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(RawContacts.CONTENT_URI, new String[] { RawContacts._ID },
                    RawContacts.CONTACT_ID + "=? AND " + RawContacts.DELETED + "=0", new String[] { String.valueOf(contactId) }, RawContacts._ID);
            if (c != null && c.moveToFirst()) return c.getLong(0);
        } finally {
            if (c != null) c.close();
        }
        return -1;
    }

    /** Reads the fields the edit screen shows. */
    static Card read(Context ctx, long contactId) {
        Card k = new Card();
        for (Datum d : data(ctx, contactId)) {
            if (StructuredName.CONTENT_ITEM_TYPE.equals(d.mime)) { if (k.name.length() == 0 && d.v1 != null) k.name = d.v1; }
            else if (Phone.CONTENT_ITEM_TYPE.equals(d.mime) && d.v1 != null) {
                if (d.type == Phone.TYPE_MOBILE && k.mobile.length() == 0) k.mobile = d.v1;
                else if (d.type == Phone.TYPE_HOME && k.home.length() == 0) k.home = d.v1;
                else if (d.type == Phone.TYPE_WORK && k.work.length() == 0) k.work = d.v1;
                else if (k.mobile.length() == 0 && d.type != Phone.TYPE_HOME && d.type != Phone.TYPE_WORK) k.mobile = d.v1;
                else k.otherPhones.add(new String[] { d.v1, String.valueOf(d.type) });
            }
            else if (Email.CONTENT_ITEM_TYPE.equals(d.mime) && k.email.length() == 0 && d.v1 != null) k.email = d.v1;
            else if (Note.CONTENT_ITEM_TYPE.equals(d.mime) && k.note.length() == 0 && d.v1 != null) k.note = d.v1;
            else if (Organization.CONTENT_ITEM_TYPE.equals(d.mime) && k.org.length() == 0 && d.v1 != null) k.org = d.v1;
        }
        return k;
    }

    private static ContentProviderOperation.Builder insertData(int backRef, long rawId, String mime) {
        ContentProviderOperation.Builder b = ContentProviderOperation.newInsert(Data.CONTENT_URI);
        if (rawId >= 0) b.withValue(Data.RAW_CONTACT_ID, rawId); else b.withValueBackReference(Data.RAW_CONTACT_ID, backRef);
        b.withValue(Data.MIMETYPE, mime);
        return b;
    }

    /**
     * Writes a contact. contactId < 0 creates a new local (account-less) contact. Existing rows are updated, emptied
     * fields are deleted. Returns the contact id, or -1 on failure.
     */
    static long save(Context ctx, long contactId, Card k) throws Exception {
        ArrayList<ContentProviderOperation> ops = new ArrayList<ContentProviderOperation>();
        long raw = -1;
        int backRef = 0;
        ArrayList<Datum> existing = new ArrayList<Datum>();
        if (contactId >= 0) {
            raw = rawContactId(ctx, contactId);
            existing = data(ctx, contactId);
        }
        if (raw < 0) {
            backRef = ops.size();
            ops.add(ContentProviderOperation.newInsert(RawContacts.CONTENT_URI)
                    .withValue(RawContacts.ACCOUNT_TYPE, null).withValue(RawContacts.ACCOUNT_NAME, null).build());
        }
        // structured name
        upsert(ops, existing, raw, backRef, StructuredName.CONTENT_ITEM_TYPE, -1, k.name, StructuredName.DISPLAY_NAME);
        upsert(ops, existing, raw, backRef, Phone.CONTENT_ITEM_TYPE, Phone.TYPE_MOBILE, k.mobile, Phone.NUMBER);
        upsert(ops, existing, raw, backRef, Phone.CONTENT_ITEM_TYPE, Phone.TYPE_HOME, k.home, Phone.NUMBER);
        upsert(ops, existing, raw, backRef, Phone.CONTENT_ITEM_TYPE, Phone.TYPE_WORK, k.work, Phone.NUMBER);
        upsert(ops, existing, raw, backRef, Email.CONTENT_ITEM_TYPE, Email.TYPE_HOME, k.email, Email.ADDRESS);
        upsert(ops, existing, raw, backRef, Note.CONTENT_ITEM_TYPE, -1, k.note, Note.NOTE);
        if (k.org.length() > 0 || hasMime(existing, Organization.CONTENT_ITEM_TYPE)) {
            upsert(ops, existing, raw, backRef, Organization.CONTENT_ITEM_TYPE, -1, k.org, Organization.COMPANY);
        }
        for (String[] p : k.otherPhones) {
            if (raw < 0 && p[0].length() > 0) {
                ops.add(insertData(backRef, raw, Phone.CONTENT_ITEM_TYPE).withValue(Phone.NUMBER, p[0]).withValue(Phone.TYPE, Integer.parseInt(p[1])).build());
            }
        }
        android.content.ContentProviderResult[] res = ctx.getContentResolver().applyBatch(ContactsContract.AUTHORITY, ops);
        if (contactId >= 0) return contactId;
        long rawNew = ContentUris.parseId(res[0].uri);
        Cursor c = null;
        try {
            c = ctx.getContentResolver().query(RawContacts.CONTENT_URI, new String[] { RawContacts.CONTACT_ID }, RawContacts._ID + "=?", new String[] { String.valueOf(rawNew) }, null);
            if (c != null && c.moveToFirst()) return c.getLong(0);
        } finally {
            if (c != null) c.close();
        }
        return -1;
    }

    private static boolean hasMime(ArrayList<Datum> ex, String mime) {
        for (Datum d : ex) if (mime.equals(d.mime)) return true;
        return false;
    }

    private static void upsert(ArrayList<ContentProviderOperation> ops, ArrayList<Datum> existing, long raw, int backRef,
            String mime, int type, String value, String column) {
        Datum hit = null;
        for (Datum d : existing) {
            if (!mime.equals(d.mime)) continue;
            if (type >= 0 && mime.equals(Phone.CONTENT_ITEM_TYPE) && d.type != type) continue;
            if (type >= 0 && mime.equals(Email.CONTENT_ITEM_TYPE) && false) continue;
            hit = d;
            break;
        }
        // The edit screen shows a "mobile" field that also stands for an untyped first phone: reuse it.
        if (hit == null && type == Phone.TYPE_MOBILE) {
            for (Datum d : existing) {
                if (Phone.CONTENT_ITEM_TYPE.equals(d.mime) && d.type != Phone.TYPE_HOME && d.type != Phone.TYPE_WORK) { hit = d; break; }
            }
        }
        if (hit != null) {
            if (value.length() == 0) {
                ops.add(ContentProviderOperation.newDelete(ContentUris.withAppendedId(Data.CONTENT_URI, hit.id)).build());
            } else {
                ops.add(ContentProviderOperation.newUpdate(ContentUris.withAppendedId(Data.CONTENT_URI, hit.id)).withValue(column, value).build());
            }
        } else if (value.length() > 0) {
            ContentProviderOperation.Builder b = insertData(backRef, raw, mime).withValue(column, value);
            if (type >= 0) b.withValue(Data.DATA2, type);
            ops.add(b.build());
        }
    }
}
