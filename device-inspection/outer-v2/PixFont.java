package org.kyf37.subdisplay;

import android.content.res.AssetManager;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HashMap;

/** Hinted 1-bit bitmap fonts for the outer panel (assets/outerfont.bin, made by make-outer-font.py). */
final class PixFont {
    static final int T26 = 0, T21 = 1, T17 = 2, S9 = 3, S9B = 4, B15 = 5, B16 = 6, R10 = 7;

    private static final class Glyph { int adv, w, h, xo, yo; byte[] bits; }
    private static final class Font { int height; final HashMap<Integer, Glyph> glyphs = new HashMap<Integer, Glyph>(); }
    private static final Font[] FONTS = new Font[8];
    private static boolean loaded;

    private PixFont() { }

    static synchronized void load(AssetManager am) {
        if (loaded) return;
        try {
            InputStream in = am.open("outerfont.bin");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) bytes.write(buf, 0, n);
            in.close();
            ByteBuffer b = ByteBuffer.wrap(bytes.toByteArray()).order(ByteOrder.LITTLE_ENDIAN);
            if (b.get() != 'P' || b.get() != 'X' || b.get() != 'F' || b.get() != '1') throw new java.io.IOException("bad magic");
            int count = b.get() & 255;
            for (int f = 0; f < count; f++) {
                int id = b.get() & 255;
                Font font = new Font();
                font.height = b.get() & 255;
                int ng = b.getShort() & 0xFFFF;
                for (int g = 0; g < ng; g++) {
                    Glyph gl = new Glyph();
                    int cp = b.getShort() & 0xFFFF;
                    gl.adv = b.get() & 255;
                    gl.w = b.get() & 255;
                    gl.h = b.get() & 255;
                    gl.xo = b.get();
                    gl.yo = b.get();
                    gl.bits = new byte[(gl.w * gl.h + 7) / 8];
                    b.get(gl.bits);
                    font.glyphs.put(cp, gl);
                }
                if (id < FONTS.length) FONTS[id] = font;
            }
            loaded = true;
        } catch (Exception e) {
            android.util.Log.e("KYF37OuterScreen", "outerfont.bin load failed", e);
        }
    }

    private static Glyph glyph(Font f, char c) {
        Glyph g = f.glyphs.get((int) c);
        return g != null ? g : f.glyphs.get((int) '?');
    }

    /** Digit/cap height in pixels. */
    static int height(int id) { return FONTS[id] == null ? 8 : FONTS[id].height; }

    static int width(int id, String s) {
        Font f = FONTS[id];
        if (f == null) return 0;
        int w = 0;
        for (int i = 0; i < s.length(); i++) { Glyph g = glyph(f, s.charAt(i)); if (g != null) w += g.adv; }
        return w;
    }

    /** Draw into a 128x36 0/1 buffer; pixels outside [clipL, clipR) are dropped; dy shifts vertically. Returns the advance. */
    static int draw(int id, String s, int x, int baseline, byte[] buf, int clipL, int clipR, int dy) {
        Font f = FONTS[id];
        if (f == null) return 0;
        int pen = x;
        for (int i = 0; i < s.length(); i++) {
            Glyph g = glyph(f, s.charAt(i));
            if (g == null) continue;
            for (int row = 0; row < g.h; row++) {
                int py = baseline + g.yo + row + dy;
                if (py < 0 || py >= OuterUi.H) continue;
                for (int col = 0; col < g.w; col++) {
                    int idx = row * g.w + col;
                    if ((g.bits[idx >> 3] & (1 << (7 - (idx & 7)))) == 0) continue;
                    int px = pen + g.xo + col;
                    if (px >= clipL && px < clipR && px >= 0 && px < OuterUi.W) buf[py * OuterUi.W + px] = 1;
                }
            }
            pen += g.adv;
        }
        return pen - x;
    }
}
