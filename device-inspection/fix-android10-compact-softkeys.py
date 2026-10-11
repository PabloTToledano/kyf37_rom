from pathlib import Path
import re
root=Path('/home/pablo/kyf37-android10')
p=root/'frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37SoftkeyBar.java'
s=p.read_text()
i=s.index('    private void image(')
head=s[:i]
# drop drawable members/loading: single-row flat bar
head=head.replace('private final Drawable base, leftUp, leftDown, center, rightUp, rightDown;\n','')
head=re.sub(r'        base = .*?rightDown = [^\n]*\n','',head,flags=re.S)
head=head.replace('/** Original KYF37 two-row softkey geometry and artwork, with current key actions. */','/** Compact single-row KYF37 softkey legend: what each physical key does right now. */')
head=head.replace('import android.graphics.drawable.Drawable;\n','')
body='''    private void label(Canvas canvas, String text, float cx, float cy, float available) {
        paint.setColor(Color.WHITE);
        paint.setTextAlign(Paint.Align.CENTER);
        float density = getResources().getDisplayMetrics().density;
        paint.setTextSize(13 * density);
        if (paint.measureText(text) > available) {
            paint.setTextSize(paint.getTextSize() * available / paint.measureText(text));
        }
        canvas.drawText(text, cx, cy - (paint.ascent() + paint.descent()) / 2, paint);
    }

    @Override protected void onDraw(Canvas canvas) {
        float width = getWidth(), height = getHeight();
        float density = getResources().getDisplayMetrics().density;
        paint.setColor(0xFF101418);
        canvas.drawRect(0, 0, width, height, paint);
        paint.setColor(0xFF39424C);
        canvas.drawRect(0, 0, width, 1 * density, paint);
        // Left column: F1 / F3. Centre: select. Right column: Menu / Home (F4).
        String[] names = {"F1", pointer ? "D-pad" : "Pointer", pointer ? "Click" : "Select",
                "Menu", "Home"};
        float[] weights = {1f, 1.3f, 1.3f, 1f, 1f};
        float total = 0; for (float w : weights) total += w;
        float x = 0;
        for (int i = 0; i < names.length; i++) {
            float w = width * weights[i] / total;
            if (i > 0) {
                paint.setColor(0xFF39424C);
                canvas.drawRect(x, 5 * density, x + 1, height - 5 * density, paint);
            }
            label(canvas, names[i], x + w / 2, height / 2 + 0.5f * density, w - 6 * density);
            x += w;
        }
    }
}
'''
p.write_text(head+body)
d=root/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_softkey_dimensions.xml'
t=d.read_text().replace('>64dp<','>28dp<')
d.write_text(t)
print(t)
