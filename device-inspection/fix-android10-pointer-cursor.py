"""KYF37 stage 3: redesigned pointer-mode cursor (F3 fallback for third-party apps). Idempotent.

Modern arrow cursor: theme-accent fill, dark 1.8 dp keyline, white halo with soft drop shadow
(readable on any background), 26 dp tall, hotspot = arrow tip.  Press feedback: arrow scales to
88 % and an accent ring expands/fades with a 140 ms ease (no animator thread needed).
Colours come from android.view.Kyf37FocusTheme (same palette as the selection outline).
"""
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/Kyf37Navigation.java')
s = p.read_text()
if 'Kyf37FocusTheme' in s:
    print('pointer cursor already redesigned')
    raise SystemExit
a = s.index('    private final class Cursor extends View {')
new_cursor = '''    private final class Cursor extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path arrow = new Path();
        private final float d;
        private boolean lastDragging;
        private long phaseStart;

        Cursor(Context context) {
            super(context);
            d = context.getResources().getDisplayMetrics().density;
            setLayerType(LAYER_TYPE_SOFTWARE, null);   // needed for the blurred shadow
            // Classic arrow, tip at (0,0), about 17 x 28 units (scaled to 26 dp tall).
            final float[] pts = {0, 0, 0, 24, 6, 18.5f, 10.5f, 28, 14, 26.5f, 9.8f, 17.2f, 17, 17.2f};
            arrow.moveTo(pts[0], pts[1]);
            for (int i = 2; i < pts.length; i += 2) arrow.lineTo(pts[i], pts[i + 1]);
            arrow.close();
        }

        @Override protected void onDraw(Canvas canvas) {
            final Context c = getContext();
            final int accent = android.view.Kyf37FocusTheme.accent(c);
            final int edge = android.view.Kyf37FocusTheme.edge(c);
            final long now = SystemClock.uptimeMillis();
            if (dragging != lastDragging) { lastDragging = dragging; phaseStart = now; }
            final float t = Math.min(1f, (now - phaseStart) / 140f);
            final float ease = t * (2 - t);
            final float press = dragging ? ease : 1 - ease;          // 0 idle .. 1 pressed
            final float unit = 26f * d / 28f;

            if (press > 0.01f) {                                      // press ring
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(5 * d);
                paint.setColor((edge & 0x00FFFFFF) | ((int) (200 * press) << 24));
                canvas.drawCircle(x, y, (9 + 10 * press) * d, paint);
                paint.setStrokeWidth(3 * d);
                paint.setColor((accent & 0x00FFFFFF) | ((int) (255 * press) << 24));
                canvas.drawCircle(x, y, (9 + 10 * press) * d, paint);
            }
            canvas.save();
            canvas.translate(x, y);
            final float scale = unit * (1f - 0.12f * press);
            canvas.scale(scale, scale);
            paint.setStrokeJoin(Paint.Join.ROUND);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(4.5f * d / scale);                   // white halo + shadow
            paint.setColor(edge);
            paint.setShadowLayer(4 * d / scale, 0, 2 * d / scale, 0x80000000);
            canvas.drawPath(arrow, paint);
            paint.clearShadowLayer();
            paint.setStrokeWidth(1.8f * d / scale);                   // dark keyline
            paint.setColor(0xFF10161C);
            canvas.drawPath(arrow, paint);
            paint.setStyle(Paint.Style.FILL);                         // accent body
            paint.setColor(accent);
            canvas.drawPath(arrow, paint);
            canvas.restore();
            if (t < 1f) postInvalidateOnAnimation();
        }
    }
}
'''
s = s[:a] + new_cursor
s = s.replace('import android.graphics.Paint;', 'import android.graphics.Paint;\nimport android.graphics.Path;')
old = '        cursor = new Cursor(context);\n'
assert old in s
s = s.replace(old, old + '''        android.view.Kyf37FocusTheme.watch(context);
        android.view.Kyf37FocusTheme.addListener(new Runnable() {
            public void run() { handler.post(new Runnable() { public void run() { cursor.invalidate(); } }); }
        });
''')
p.write_text(s)
print('pointer cursor redesigned (theme-aware arrow with press feedback)')
