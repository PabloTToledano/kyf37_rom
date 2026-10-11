package org.kyf37.tama;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.WindowManager;

/** Keypad virtual pet. Everything lives in {@link TamaView}; the activity only forwards keys and lifecycle. */
public final class Tama extends Activity {
    private TamaView view;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        view = new TamaView(this);
        setContentView(view);
        view.requestFocus();
    }

    @Override protected void onResume() { super.onResume(); view.resumeGame(); }
    @Override protected void onPause() { view.pauseGame(); super.onPause(); }

    @Override public boolean onKeyDown(int code, KeyEvent e) {
        if (view.onGameKey(code, e)) return true;
        return super.onKeyDown(code, e);
    }

    @Override public boolean onKeyUp(int code, KeyEvent e) {
        if (view.onGameKeyUp(code, e)) return true;
        return super.onKeyUp(code, e);
    }

    @Override public void onBackPressed() {
        if (!view.onBack()) super.onBackPressed();
    }

    SharedPreferences store() { return getSharedPreferences("tama", MODE_PRIVATE); }
}
