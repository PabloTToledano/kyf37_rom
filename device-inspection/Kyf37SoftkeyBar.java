package com.android.systemui.statusbar.phone;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.view.View;
import com.android.systemui.R;

/** Original KYF37 two-row softkey geometry and artwork, with current key actions. */
public final class Kyf37SoftkeyBar extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Drawable base, leftUp, leftDown, center, rightUp, rightDown;
    private boolean pointer;
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            pointer = intent.getBooleanExtra("enabled", false);
            invalidate();
        }
    };

    public Kyf37SoftkeyBar(Context context) {
        super(context);
        base = context.getDrawable(R.drawable.k_i_co_btn_softkey_base);
        leftUp = context.getDrawable(R.drawable.k_c_co_btn_softkey_left_up_normal);
        leftDown = context.getDrawable(R.drawable.k_c_co_btn_softkey_left_down_normal);
        center = context.getDrawable(R.drawable.k_c_co_btn_softkey_center_normal);
        rightUp = context.getDrawable(R.drawable.k_c_co_btn_softkey_right_up_normal);
        rightDown = context.getDrawable(R.drawable.k_c_co_btn_softkey_right_down_normal);
        setFocusable(false);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        setContentDescription("Physical keys: F1, Menu, Select, F3 pointer, F4 Home");
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        getContext().registerReceiver(receiver, new IntentFilter("org.kyf37.POINTER_CHANGED"),
                android.Manifest.permission.STATUS_BAR, null);
    }

    @Override protected void onDetachedFromWindow() {
        getContext().unregisterReceiver(receiver);
        super.onDetachedFromWindow();
    }

    private void image(Canvas canvas, Drawable drawable, RectF bounds) {
        drawable.setBounds(Math.round(bounds.left), Math.round(bounds.top),
                Math.round(bounds.right), Math.round(bounds.bottom));
        drawable.draw(canvas);
    }

    private void label(Canvas canvas, String text, RectF bounds) {
        paint.setColor(Color.WHITE);
        paint.setTextSize(24 * getResources().getDisplayMetrics().density);
        paint.setTextAlign(Paint.Align.CENTER);
        float available = bounds.width() - 12 * getResources().getDisplayMetrics().density;
        if (paint.measureText(text) > available) {
            paint.setTextSize(paint.getTextSize() * available / paint.measureText(text));
        }
        canvas.save();
        canvas.clipRect(bounds);
        canvas.drawText(text, bounds.centerX(),
                bounds.centerY() - (paint.ascent() + paint.descent()) / 2, paint);
        canvas.restore();
    }

    @Override protected void onDraw(Canvas canvas) {
        float width = getWidth(), height = getHeight();
        // Stock dimensions: 116dp side columns, 88dp center; two 32dp rows.
        float left = width * 116f / 320f, right = width * 204f / 320f;
        RectF lu = new RectF(0, 0, left, height / 2);
        RectF ld = new RectF(0, height / 2, left, height);
        RectF middle = new RectF(left, 0, right, height);
        RectF ru = new RectF(right, 0, width, height / 2);
        RectF rd = new RectF(right, height / 2, width, height);
        image(canvas, base, new RectF(0, 0, width, height));
        image(canvas, leftUp, lu); image(canvas, leftDown, ld);
        image(canvas, center, middle);
        image(canvas, rightUp, ru); image(canvas, rightDown, rd);
        label(canvas, "F1", lu); label(canvas, pointer ? "D-pad" : "Pointer", ld);
        label(canvas, pointer ? "Click" : "Select", middle);
        label(canvas, "Menu", ru); label(canvas, "Home", rd);
    }
}
