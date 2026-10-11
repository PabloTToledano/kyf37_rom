package org.kyf37.subdisplay;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;

/** Java renderer for the 128x36 1-bit outer panel: clock, call and notification screens. Pixels are 0/1 bytes, row-major. */
final class OuterUi {
    static final int W = 128, H = 36;
    static final int K_NOTIF = 0, K_MESSAGE = 1, K_RING = 2, K_INCALL = 3, K_MISSED = 4;
    private static final Bitmap BMP = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888);
    private static final Canvas CV = new Canvas(BMP);
    private static final Paint P = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final Typeface BOLD = Typeface.create("sans-serif-condensed", Typeface.BOLD);
    private static final Typeface NORMAL = Typeface.create("sans-serif-condensed", Typeface.NORMAL);

    private static final byte[] TXT = new byte[W * H];
    private static int dy;

    private OuterUi() { }

    private static void begin() {
        CV.setMatrix(null);
        CV.drawColor(Color.BLACK);
        P.setColor(Color.WHITE);
        P.setStyle(Paint.Style.FILL);
        P.setStrokeWidth(1f);
        java.util.Arrays.fill(TXT, (byte) 0);
        dy = 0;
    }

    private static byte[] end() {
        int[] px = new int[W * H];
        BMP.getPixels(px, 0, W, 0, 0, W, H);
        byte[] out = new byte[W * H];
        for (int i = 0; i < out.length; i++) out[i] = (byte) ((((px[i] >> 16) & 255) > 110 || TXT[i] != 0) ? 1 : 0);
        return out;
    }

    static byte[] pack(byte[] pixels) {
        byte[] packed = new byte[W * H / 8];
        for (int i = 0; i < pixels.length; i++) if (pixels[i] != 0) packed[i / 8] |= (byte) (1 << (7 - i % 8));
        return packed;
    }

    private static int text(int font, String s, int x, int baseline) { return PixFont.draw(font, s, x, baseline, TXT, 0, W, dy); }
    private static int textClip(int font, String s, int x, int baseline, int l, int r) { return PixFont.draw(font, s, x, baseline, TXT, l, r, dy); }

    // ------------------------------------------------------------------------------------------ idle clock
    /** Clock layer. With mascot the layer owns x<96 (the mascot owns the rest), without it the whole panel width. */
    static byte[] clock(int hour, int minute, int second, int size, boolean fmt12, boolean seconds, int batt,
                        int battery, int unread, String dateLong, String dateShort, boolean mascot) {
        begin();
        int maxW = mascot ? 94 : 126;
        int h = hour;
        boolean pm = false;
        if (fmt12) { pm = hour >= 12; h = hour % 12; if (h == 0) h = 12; }
        String t = (fmt12 ? String.valueOf(h) : String.format("%02d", h)) + ":" + String.format("%02d", minute);
        String secs = seconds ? String.format("%02d", second) : null;
        int font = size <= 0 ? PixFont.T17 : (size == 1 ? PixFont.T21 : PixFont.T26);
        while (true) {
            int extra = (secs != null ? 3 + PixFont.width(PixFont.S9B, secs) : 0) + (fmt12 ? 3 + PixFont.width(PixFont.S9B, "AM") : 0);
            if (PixFont.width(font, t) + extra <= maxW - 3 || font == PixFont.T17) break;
            font = font == PixFont.T26 ? PixFont.T21 : PixFont.T17;
        }
        int hgt = PixFont.height(font);
        int baseline = Math.max(hgt + 1, (27 - hgt) / 2 + hgt);
        int x = 3;
        int adv = text(font, t, x, baseline);
        int after = x + adv + 3;
        if (secs != null) { text(PixFont.S9B, secs, after, baseline); after += PixFont.width(PixFont.S9B, secs) + 3; }
        if (fmt12) text(PixFont.S9B, pm ? "PM" : "AM", after, baseline - hgt + PixFont.height(PixFont.S9B));
        // bottom row: date, unread envelope, battery
        int rowBase = 35;
        int right = maxW - 2;
        int batteryLeft = right;
        if ((batt & 3) != 0) {
            boolean icon = (batt & 1) != 0, pct = (batt & 2) != 0;
            if (pct) { String s = battery + "%"; int w = PixFont.width(PixFont.S9B, s); text(PixFont.S9B, s, right - w, rowBase); batteryLeft = right - w - 3; }
            if (icon) {
                float ix = batteryLeft - 15;
                P.setStyle(Paint.Style.STROKE);
                CV.drawRect(ix + 0.5f, 28.5f, ix + 12.5f, 34.5f, P);
                P.setStyle(Paint.Style.FILL);
                CV.drawRect(ix + 13f, 30f, ix + 14.5f, 33f, P);
                CV.drawRect(ix + 2f, 30f, ix + 2f + 9f * battery / 100f, 33f, P);
                batteryLeft = (int) ix - 3;
            }
        }
        String d = dateLong;
        if (3 + PixFont.width(PixFont.S9, d) > batteryLeft - (unread > 0 ? 22 : 0)) d = dateShort;
        int dw = text(PixFont.S9, d, 3, rowBase);
        if (unread > 0) {
            int ux = 3 + dw + 6;
            if (ux + 20 <= batteryLeft) { envelope(ux + 5, 31.5f, 10, 7); text(PixFont.S9B, String.valueOf(Math.min(unread, 99)), ux + 12, rowBase); }
        }
        return end();
    }

    // ------------------------------------------------------------------------------------------ glyphs
    private static void envelope(float cx, float cy, float w, float h) {
        P.setStyle(Paint.Style.STROKE);
        P.setStrokeWidth(1.2f);
        CV.drawRect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, P);
        CV.drawLine(cx - w / 2, cy - h / 2, cx, cy + h / 6, P);
        CV.drawLine(cx + w / 2, cy - h / 2, cx, cy + h / 6, P);
        P.setStyle(Paint.Style.FILL);
        P.setStrokeWidth(1f);
    }

    private static void bell(float cx, float cy, float swing) {
        CV.save();
        CV.rotate(swing, cx, cy - 8);
        Path b = new Path();
        b.moveTo(cx - 8, cy + 6);
        b.quadTo(cx - 6, cy + 3, cx - 6, cy - 2);
        b.quadTo(cx - 6, cy - 9, cx, cy - 9);
        b.quadTo(cx + 6, cy - 9, cx + 6, cy - 2);
        b.quadTo(cx + 6, cy + 3, cx + 8, cy + 6);
        b.close();
        CV.drawPath(b, P);
        CV.drawCircle(cx, cy + 9, 2.2f, P);
        CV.drawCircle(cx, cy - 10, 1.5f, P);
        CV.restore();
    }

    private static void handset(float cx, float cy, float tilt) {
        CV.save();
        CV.rotate(-40 + tilt, cx, cy);
        CV.drawRect(cx - 2, cy - 9, cx + 1, cy + 9, P);
        CV.drawRect(cx - 2, cy - 9, cx + 6, cy - 4, P);
        CV.drawRect(cx - 2, cy + 4, cx + 6, cy + 9, P);
        CV.restore();
    }

    private static void waves(float cx, float cy, int tick) {
        P.setStyle(Paint.Style.STROKE);
        P.setStrokeWidth(1.5f);
        int n = 1 + (tick / 3) % 3;
        for (int i = 0; i < n; i++) {
            float r = 8 + i * 4.5f;
            CV.drawArc(new RectF(cx - r, cy - r, cx + r, cy + r), -50, 100, false, P);
        }
        P.setStyle(Paint.Style.FILL);
        P.setStrokeWidth(1f);
    }

    // ------------------------------------------------------------------------------------------ alerts
    private static void marquee(String s, int x, int baseline, int w, int font, int tick) {
        int tw = PixFont.width(font, s);
        if (tw <= w) { textClip(font, s, x, baseline, x, x + w); return; }
        int gap = 22, cycle = tw + gap;
        int off = (Math.max(0, tick - 10) * 2) % cycle;
        textClip(font, s, x - off, baseline, x, x + w);
        textClip(font, s, x - off + cycle, baseline, x, x + w);
    }

    /** One alert frame. tick counts 10 fps frames since the alert began; remaining is 0..100 (notification countdown). */
    static byte[] alert(int kind, String title, String body, int tick, int remaining) {
        begin();
        int slide = Math.max(0, H - tick * 6); // slide up on arrival
        CV.translate(0, slide);
        dy = slide;
        float ix = 13f, iy = 18f;
        switch (kind) {
            case K_RING:
                handset(ix - 3, iy, (tick % 2 == 0) ? -8 : 8);
                waves(ix + 3, iy - 1, tick);
                break;
            case K_INCALL:
                handset(ix - 3, iy, 0);
                break;
            case K_MISSED:
                handset(ix - 3, iy, 0);
                P.setStrokeWidth(2f);
                CV.drawLine(ix + 3, iy - 9, ix + 11, iy - 1, P);
                CV.drawLine(ix + 11, iy - 9, ix + 3, iy - 1, P);
                P.setStrokeWidth(1f);
                break;
            case K_MESSAGE:
                envelope(ix, iy, 17, 12);
                if (tick % 6 < 3) CV.drawCircle(ix + 9, iy - 8, 2.2f, P);
                break;
            default:
                bell(ix, iy, tick < 14 ? (float) (14 * Math.sin(tick * 1.1) * (14 - tick) / 14) : 0);
        }
        int tx = 28, tw = W - tx - 1;
        if (body == null || body.isEmpty()) {
            marquee(title, tx, 24, tw, PixFont.B16, tick);
        } else {
            marquee(title, tx, 15, tw, PixFont.B15, tick);
            marquee(body, tx, 30, tw, PixFont.R10, tick);
        }
        if (kind <= K_MESSAGE || kind == K_MISSED) CV.drawRect(0, 35, W * remaining / 100f, 36, P);
        return end();
    }
}
