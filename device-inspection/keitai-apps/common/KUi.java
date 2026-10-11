package @PKG@;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Context;
import android.database.ContentObserver;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Handler;
import android.provider.ContactsContract.PhoneLookup;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextClock;
import android.widget.TextView;
import android.widget.Toast;
import java.util.HashMap;

/**
 * Shared keitai look for the KYF37 Phone / Messages / Contacts apps: header strip (title + clock), plain
 * numbered list rows, one-row soft-key hint footer, numbered menus and two-step confirmations.
 * Selection is drawn by the framework focus theme (android.view.Kyf37FocusTheme); on older ROMs a blue
 * selector is used. Colours follow Settings.Global kyf37_icon_theme (0 Standard, 1 Pastel Star, 2 Sky Star).
 * This file is copied into every app by device-inspection/fix-android10-keitai-apps.py (@PKG@ = package).
 */
public final class KUi {
    private KUi() { }

    public static final int BG = 0xFF10151B;
    public static final int DIVIDER = 0xFF26303A;
    public static final int TEXT = 0xFFFFFFFF;
    public static final int TEXT2 = 0xFFB8C2CC;
    public static final int RED = 0xFFFF6B6B;
    public static final int GREEN = 0xFF5FD38D;

    public static int theme(Context c) {
        try { return Settings.Global.getInt(c.getContentResolver(), "kyf37_icon_theme", 1); }
        catch (RuntimeException e) { return 1; }
    }

    /** Header strip colour per Appearance icon theme. */
    public static int headerColor(Context c) {
        switch (theme(c)) {
            case 0: return 0xFF1B2733;
            case 2: return 0xFF2A78B8;
            default: return 0xFFA8467A;
        }
    }

    /** Colour for digits / accents on the dark body. */
    public static int accent(Context c) {
        switch (theme(c)) {
            case 0: return 0xFF6AA9FF;
            case 2: return 0xFF8FD3FF;
            default: return 0xFFFFA6D1;
        }
    }

    public static float dp(Context c) { return c.getResources().getDisplayMetrics().density; }
    public static int px(Context c, float v) { return (int) (v * dp(c) + 0.5f); }

    public static void toast(Context c, String s) { Toast.makeText(c, s, Toast.LENGTH_SHORT).show(); }

    /** 0..9 for a digit key, -1 otherwise. */
    public static int digit(int keyCode) {
        if (keyCode >= KeyEvent.KEYCODE_0 && keyCode <= KeyEvent.KEYCODE_9) return keyCode - KeyEvent.KEYCODE_0;
        if (keyCode >= KeyEvent.KEYCODE_NUMPAD_0 && keyCode <= KeyEvent.KEYCODE_NUMPAD_9) return keyCode - KeyEvent.KEYCODE_NUMPAD_0;
        return -1;
    }

    public static boolean isMenuKey(int k) { return k == KeyEvent.KEYCODE_MENU || k == KeyEvent.KEYCODE_F1; }

    // ----------------------------------------------------------------------------------------------- screen

    /** Header + body + footer scaffold. Also re-themes itself when the Appearance setting changes. */
    public static final class Screen {
        public final LinearLayout root;
        public final LinearLayout header;
        public final TextView title;
        public final TextView clock;
        public final FrameLayout body;
        public final TextView hintL, hintC, hintR;
        private final Activity act;
        private ContentObserver observer;

        Screen(Activity a, String t) {
            act = a;
            Context c = a;
            root = new LinearLayout(c);
            root.setOrientation(LinearLayout.VERTICAL);
            root.setBackgroundColor(BG);
            header = new LinearLayout(c);
            header.setOrientation(LinearLayout.HORIZONTAL);
            header.setGravity(Gravity.CENTER_VERTICAL);
            header.setPadding(px(c, 12), px(c, 6), px(c, 12), px(c, 6));
            header.setBackgroundColor(headerColor(c));
            title = new TextView(c);
            title.setTextColor(TEXT);
            title.setTextSize(20);
            title.setTypeface(Typeface.DEFAULT_BOLD);
            title.setSingleLine(true);
            title.setEllipsize(TextUtils.TruncateAt.END);
            title.setText(t);
            header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            clock = new TextClock(c);
            ((TextClock) clock).setFormat12Hour("h:mm");
            ((TextClock) clock).setFormat24Hour("HH:mm");
            clock.setTextColor(TEXT);
            clock.setTextSize(16);
            header.addView(clock, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            root.addView(header, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, px(c, 44)));
            body = new FrameLayout(c);
            root.addView(body, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
            View line = new View(c);
            line.setBackgroundColor(DIVIDER);
            root.addView(line, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 1));
            LinearLayout foot = new LinearLayout(c);
            foot.setOrientation(LinearLayout.HORIZONTAL);
            foot.setBackgroundColor(0xFF0B0F13);
            foot.setPadding(px(c, 10), px(c, 3), px(c, 10), px(c, 3));
            hintL = hint(c, Gravity.LEFT | Gravity.CENTER_VERTICAL);
            hintC = hint(c, Gravity.CENTER);
            hintR = hint(c, Gravity.RIGHT | Gravity.CENTER_VERTICAL);
            foot.addView(hintL, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            foot.addView(hintC, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            foot.addView(hintR, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            root.addView(foot, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, px(c, 30)));
        }

        private static TextView hint(Context c, int gravity) {
            TextView t = new TextView(c);
            t.setTextSize(13);
            t.setTextColor(0xFFD6DEE6);
            t.setSingleLine(true);
            t.setEllipsize(TextUtils.TruncateAt.END);
            t.setGravity(gravity);
            return t;
        }

        /** Bottom one-row soft-key legend; pass null/"" to blank a slot. */
        public void hints(String left, String centre, String right) {
            hintL.setText(left == null ? "" : left);
            hintC.setText(centre == null ? "" : centre);
            hintR.setText(right == null ? "" : right);
        }

        public void setTitle(String t) { title.setText(t); }

        void watch() {
            observer = new ContentObserver(new Handler()) {
                @Override public void onChange(boolean self) {
                    header.setBackgroundColor(headerColor(act));
                    act.recreate();
                }
            };
            try {
                act.getContentResolver().registerContentObserver(Settings.Global.getUriFor("kyf37_icon_theme"), false, observer);
            } catch (RuntimeException e) { observer = null; }
        }

        public void unwatch() {
            if (observer != null) {
                try { act.getContentResolver().unregisterContentObserver(observer); } catch (RuntimeException e) { }
                observer = null;
            }
        }
    }

    public static Screen screen(Activity a, String title) {
        Screen s = new Screen(a, title);
        s.watch();
        a.setContentView(s.root);
        return s;
    }

    // ----------------------------------------------------------------------------------------------- lists

    public static ListView list(Context c) {
        ListView l = new ListView(c);
        l.setDivider(new ColorDrawable(DIVIDER));
        l.setDividerHeight(1);
        l.setSelector(new ColorDrawable(Kyf37FocusCompat.has() ? 0 : 0x553D8BFF));
        l.setItemsCanFocus(false);
        l.setCacheColorHint(0);
        l.setBackgroundColor(BG);
        l.setVerticalScrollBarEnabled(false);
        return l;
    }

    public static final class Row {
        /** Left column: a digit, a short tag ("OUT") or empty. */
        public String num = "";
        public int numColor = 0;
        public String title = "";
        public String sub = "";
        public String right = "";
        /** One or two letters in a coloured circle; null = no avatar. */
        public String avatar;
        public boolean bold;
        /** Lines of title text (message bodies use up to 6). */
        public int titleLines = 1;
        public int titleColor = TEXT;
        public int rightColor = TEXT2;
    }

    private static final int[] AVATAR = {0xFFE57373, 0xFFBA68C8, 0xFF7986CB, 0xFF4FC3F7, 0xFF4DB6AC, 0xFF81C784, 0xFFFFB74D, 0xFFA1887F};

    public static int avatarColor(String key) {
        if (key == null) return AVATAR[0];
        return AVATAR[(key.hashCode() & 0x7fffffff) % AVATAR.length];
    }

    public static String initial(String name) {
        if (name == null) return "?";
        for (int i = 0; i < name.length(); i++) {
            char ch = name.charAt(i);
            if (Character.isLetterOrDigit(ch)) return String.valueOf(Character.toUpperCase(ch));
        }
        return "#";
    }

    /** Adapter that renders {@link Row}s in the shared keitai row layout. */
    public abstract static class Rows extends BaseAdapter {
        private final Context ctx;
        private final boolean avatars;
        protected Rows(Context c, boolean avatars) { ctx = c; this.avatars = avatars; }
        protected abstract Row row(int pos);
        @Override public Object getItem(int i) { return i; }
        @Override public long getItemId(int i) { return i; }

        @Override public View getView(int pos, View convert, ViewGroup parent) {
            LinearLayout v;
            TextView num, title, sub, right, av;
            if (convert == null) {
                v = new LinearLayout(ctx);
                v.setOrientation(LinearLayout.HORIZONTAL);
                v.setGravity(Gravity.CENTER_VERTICAL);
                v.setPadding(px(ctx, 8), px(ctx, 6), px(ctx, 10), px(ctx, 6));
                v.setMinimumHeight(px(ctx, 52));
                v.setWillNotDraw(false);
                num = new TextView(ctx);
                num.setId(1);
                num.setTextSize(18);
                num.setTypeface(Typeface.DEFAULT_BOLD);
                num.setGravity(Gravity.CENTER);
                v.addView(num, new LinearLayout.LayoutParams(px(ctx, 34), ViewGroup.LayoutParams.WRAP_CONTENT));
                av = new TextView(ctx);
                av.setId(5);
                av.setGravity(Gravity.CENTER);
                av.setTextColor(Color.WHITE);
                av.setTextSize(17);
                av.setTypeface(Typeface.DEFAULT_BOLD);
                LinearLayout.LayoutParams alp = new LinearLayout.LayoutParams(px(ctx, 38), px(ctx, 38));
                alp.rightMargin = px(ctx, 10);
                v.addView(av, alp);
                LinearLayout col = new LinearLayout(ctx);
                col.setOrientation(LinearLayout.VERTICAL);
                title = new TextView(ctx);
                title.setId(2);
                title.setTextSize(18);
                title.setSingleLine(true);
                title.setEllipsize(TextUtils.TruncateAt.END);
                sub = new TextView(ctx);
                sub.setId(3);
                sub.setTextSize(13);
                sub.setTextColor(TEXT2);
                sub.setSingleLine(true);
                sub.setEllipsize(TextUtils.TruncateAt.END);
                col.addView(title);
                col.addView(sub);
                v.addView(col, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
                right = new TextView(ctx);
                right.setId(4);
                right.setTextSize(13);
                right.setSingleLine(true);
                LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                rlp.leftMargin = px(ctx, 6);
                v.addView(right, rlp);
                v.setLayoutParams(new android.widget.AbsListView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            } else {
                v = (LinearLayout) convert;
            }
            num = (TextView) v.findViewById(1);
            title = (TextView) v.findViewById(2);
            sub = (TextView) v.findViewById(3);
            right = (TextView) v.findViewById(4);
            av = (TextView) v.findViewById(5);
            Row r = row(pos);
            num.setText(r.num);
            num.setTextSize(r.num.length() > 2 ? 11 : 18);
            num.setTextColor(r.numColor != 0 ? r.numColor : accent(ctx));
            title.setText(r.title);
            if (r.titleLines <= 1) { title.setSingleLine(true); } else { title.setSingleLine(false); title.setMaxLines(r.titleLines); }
            title.setTextColor(r.titleColor);
            title.setTypeface(r.bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
            sub.setText(r.sub);
            sub.setVisibility(r.sub == null || r.sub.length() == 0 ? View.GONE : View.VISIBLE);
            right.setText(r.right);
            right.setTextColor(r.rightColor);
            if (avatars && r.avatar != null) {
                av.setVisibility(View.VISIBLE);
                av.setText(r.avatar);
                GradientDrawable g = new GradientDrawable();
                g.setShape(GradientDrawable.OVAL);
                g.setColor(avatarColor(r.avatar + r.title));
                av.setBackground(g);
            } else {
                av.setVisibility(avatars ? View.INVISIBLE : View.GONE);
            }
            return v;
        }
    }

    // ----------------------------------------------------------------------------------------------- dialogs

    public interface Pick { void pick(int index); }

    private static AlertDialog.Builder builder(Context c) {
        return new AlertDialog.Builder(c, android.R.style.Theme_DeviceDefault_Dialog_Alert);
    }

    /** Numbered menu: OK picks the selected row, a digit key picks that row directly. Clear/Back cancels. */
    public static Dialog menu(final Activity a, String title, final String[] items, final Pick pick) {
        String[] labels = new String[items.length];
        for (int i = 0; i < items.length; i++) labels[i] = (i < 9 ? (i + 1) + "   " : "     ") + items[i];
        final AlertDialog d = builder(a).setTitle(title).setItems(labels, (dlg, which) -> pick.pick(which)).create();
        d.setOnKeyListener((dlg, code, ev) -> {
            if (ev.getAction() != KeyEvent.ACTION_DOWN || ev.getRepeatCount() != 0) return false;
            int n = digit(code);
            if (n >= 1 && n <= items.length && n <= 9) {
                d.dismiss();
                pick.pick(n - 1);
                return true;
            }
            return false;
        });
        d.show();
        return d;
    }

    /** Yes/No question. Focus starts on "No" so a stray OK never confirms. */
    public static void confirm(Activity a, String title, String message, String yes, final Runnable onYes) {
        final AlertDialog d = builder(a).setTitle(title).setMessage(message)
                .setPositiveButton(yes, (dlg, w) -> onYes.run())
                .setNegativeButton("No", null).create();
        d.show();
        try { d.getButton(AlertDialog.BUTTON_NEGATIVE).requestFocus(); } catch (RuntimeException e) { }
    }

    /** Destructive actions: two consecutive confirmations. */
    public static void confirmTwice(final Activity a, final String what, final String yes, final Runnable onYes) {
        confirm(a, "Delete", what + "?", yes, () ->
                confirm(a, "Are you sure?", "This cannot be undone.", yes, onYes));
    }

    // ----------------------------------------------------------------------------------------------- data helpers

    private static final HashMap<String, String> NAME_CACHE = new HashMap<String, String>();

    /** Display name of the contact owning the number, or null. Cached for the process lifetime of the screen. */
    public static String nameFor(Context c, String number) {
        if (number == null || number.length() == 0) return null;
        if (NAME_CACHE.containsKey(number)) return NAME_CACHE.get(number);
        String name = null;
        Cursor cur = null;
        try {
            Uri u = Uri.withAppendedPath(PhoneLookup.CONTENT_FILTER_URI, Uri.encode(number));
            cur = c.getContentResolver().query(u, new String[] { PhoneLookup.DISPLAY_NAME }, null, null, null);
            if (cur != null && cur.moveToFirst()) name = cur.getString(0);
        } catch (RuntimeException e) {
            name = null;
        } finally {
            if (cur != null) cur.close();
        }
        NAME_CACHE.put(number, name);
        return name;
    }

    public static void forgetNames() { NAME_CACHE.clear(); }

    public static String nameOrNumber(Context c, String number) {
        String n = nameFor(c, number);
        if (n != null && n.length() > 0) return n;
        return number == null || number.length() == 0 ? "Unknown" : number;
    }

    /** Short human date: HH:mm today, "d MMM" this year, else "d MMM yy". */
    public static String when(Context c, long ms) {
        if (ms <= 0) return "";
        java.util.Calendar now = java.util.Calendar.getInstance();
        java.util.Calendar t = java.util.Calendar.getInstance();
        t.setTimeInMillis(ms);
        java.text.SimpleDateFormat f;
        if (now.get(java.util.Calendar.YEAR) == t.get(java.util.Calendar.YEAR)
                && now.get(java.util.Calendar.DAY_OF_YEAR) == t.get(java.util.Calendar.DAY_OF_YEAR)) {
            f = new java.text.SimpleDateFormat(android.text.format.DateFormat.is24HourFormat(c) ? "HH:mm" : "h:mm a");
        } else if (now.get(java.util.Calendar.YEAR) == t.get(java.util.Calendar.YEAR)) {
            f = new java.text.SimpleDateFormat("d MMM");
        } else {
            f = new java.text.SimpleDateFormat("d MMM yy");
        }
        return f.format(new java.util.Date(ms));
    }

    public static String duration(long seconds) {
        if (seconds < 0) seconds = 0;
        long h = seconds / 3600, m = (seconds / 60) % 60, s = seconds % 60;
        return h > 0 ? String.format("%d:%02d:%02d", h, m, s) : String.format("%d:%02d", m, s);
    }
}
