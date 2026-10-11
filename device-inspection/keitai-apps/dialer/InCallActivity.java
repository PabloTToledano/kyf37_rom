package org.kyf37.dialer;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.telecom.Call;
import android.telecom.CallAudioState;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;
import android.telecom.VideoProfile;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * In-call screen, fully keypad driven.
 * Incoming: Call or OK answers, End or Clear rejects, F1 = reject with a text message.
 * Ongoing: digits send DTMF, OK mute, Up speaker, Down hold, F1 menu (swap, merge, add call, ...), End hangs up,
 * Clear sends the screen to the background (the call continues; the notification brings it back).
 */
public final class InCallActivity extends Activity implements KeitaiInCallService.Listener {
    private static final String[] CANNED = {
            "Can't talk now. What's up?", "I'll call you right back.", "I'll call you later.", "Can't talk now. Call me later?" };

    private final Handler handler = new Handler();
    private KUi.Screen screen;
    private TextView state, avatar, name, number, timer, flags, extra, dtmf;
    private final StringBuilder dtmfText = new StringBuilder();
    private boolean closing;
    private int lastKey;

    private final Runnable tick = new Runnable() {
        @Override public void run() { render(); handler.postDelayed(this, 1000); }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        setShowWhenLocked(true);
        setTurnScreenOn(true);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        screen = KUi.screen(this, "Call");
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setGravity(Gravity.CENTER_HORIZONTAL);
        col.setPadding(KUi.px(this, 12), KUi.px(this, 10), KUi.px(this, 12), 0);
        state = text(col, 16, KUi.accent(this), false);
        avatar = new TextView(this);
        avatar.setGravity(Gravity.CENTER);
        avatar.setTextColor(Color.WHITE);
        avatar.setTextSize(40);
        avatar.setTypeface(Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams alp = new LinearLayout.LayoutParams(KUi.px(this, 96), KUi.px(this, 96));
        alp.topMargin = KUi.px(this, 8);
        alp.bottomMargin = KUi.px(this, 8);
        col.addView(avatar, alp);
        name = text(col, 28, Color.WHITE, true);
        number = text(col, 17, KUi.TEXT2, false);
        timer = text(col, 26, KUi.accent(this), true);
        flags = text(col, 15, KUi.GREEN, true);
        extra = text(col, 15, KUi.TEXT2, false);
        dtmf = text(col, 20, Color.WHITE, false);
        screen.body.addView(col);
        KeitaiInCallService.addListener(this);
        render();
    }

    private TextView text(LinearLayout col, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setGravity(Gravity.CENTER);
        t.setSingleLine(true);
        t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        col.addView(t, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return t;
    }

    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        closing = false;
        render();
    }

    @Override protected void onResume() {
        super.onResume();
        handler.removeCallbacks(tick);
        handler.post(tick);
    }

    @Override protected void onPause() {
        handler.removeCallbacks(tick);
        super.onPause();
    }

    @Override protected void onDestroy() {
        KeitaiInCallService.removeListener(this);
        screen.unwatch();
        super.onDestroy();
    }

    @Override public void onCallsChanged() {
        runOnUiThread(new Runnable() { @Override public void run() { render(); } });
    }

    // ------------------------------------------------------------------------------------------ rendering

    private void render() {
        Call p = KeitaiInCallService.primary();
        if (p == null) {
            if (!closing) { closing = true; handler.postDelayed(new Runnable() { @Override public void run() {
                if (!KeitaiInCallService.hasCalls()) finish(); else { closing = false; render(); } } }, 1200); }
            if (state.getText().length() == 0) state.setText("Call ended");
            return;
        }
        int st = p.getState();
        String nm = CallUi.displayName(this, p);
        String num = CallUi.number(p);
        state.setText(CallUi.stateText(p));
        state.setTextColor(st == Call.STATE_DISCONNECTED ? KUi.RED : KUi.accent(this));
        name.setText(nm);
        number.setText(nm.equals(num) ? "" : num);
        avatar.setText(KUi.initial(KUi.nameFor(this, num) != null ? nm : "#"));
        GradientDrawable g = new GradientDrawable();
        g.setShape(GradientDrawable.OVAL);
        g.setColor(KUi.avatarColor(nm));
        avatar.setBackground(g);
        long t0 = p.getDetails().getConnectTimeMillis();
        timer.setText((st == Call.STATE_ACTIVE || st == Call.STATE_HOLDING) && t0 > 0
                ? KUi.duration((System.currentTimeMillis() - t0) / 1000) : "");
        CallAudioState a = KeitaiInCallService.audio();
        StringBuilder f = new StringBuilder();
        if (a != null && a.isMuted()) f.append("MUTED  ");
        if (a != null && a.getRoute() == CallAudioState.ROUTE_SPEAKER) f.append("SPEAKER  ");
        if (a != null && a.getRoute() == CallAudioState.ROUTE_BLUETOOTH) f.append("BLUETOOTH  ");
        if (st == Call.STATE_HOLDING) f.append("ON HOLD");
        flags.setText(f.toString().trim());
        List<Call> all = KeitaiInCallService.calls();
        StringBuilder e = new StringBuilder();
        for (Call c : all) {
            if (c == p || c.getParent() != null) continue;
            if (e.length() > 0) e.append("\n");
            e.append(c.getState() == Call.STATE_RINGING ? "Waiting: " : c.getState() == Call.STATE_HOLDING ? "On hold: " : "Also: ")
                    .append(CallUi.displayName(this, c));
        }
        extra.setSingleLine(false);
        extra.setText(e.toString());
        dtmf.setText(dtmfText.toString());
        updateHints(p, st);
    }

    private void updateHints(Call p, int st) {
        boolean waiting = false;
        boolean held = false;
        for (Call c : KeitaiInCallService.calls()) {
            if (c == p) continue;
            if (c.getState() == Call.STATE_RINGING) waiting = true;
            if (c.getState() == Call.STATE_HOLDING) held = true;
        }
        if (st == Call.STATE_RINGING) {
            screen.hints("F1 Reject+text", "Call  Answer", "End  Reject");
            screen.setTitle(waiting || held ? "Call waiting" : "Incoming call");
        } else if (st == Call.STATE_DISCONNECTED) {
            screen.hints("", "", "End  Close");
            screen.setTitle("Call");
        } else if (st == Call.STATE_SELECT_PHONE_ACCOUNT) {
            screen.hints("", "OK  Choose line", "End  Cancel");
        } else if (st == Call.STATE_HOLDING) {
            screen.hints("F1 Menu", "OK  Resume", "End  Hang up");
            screen.setTitle("On hold");
        } else {
            screen.hints("F1 Menu", "OK  Mute", "End  Hang up");
            screen.setTitle(st == Call.STATE_DIALING || st == Call.STATE_CONNECTING ? "Calling" : "On call");
        }
    }

    // ------------------------------------------------------------------------------------------ actions

    private void answer(Call p) { p.answer(VideoProfile.STATE_AUDIO_ONLY); }

    private void rejectWithText(final Call p) {
        KUi.menu(this, "Reject with message", CANNED, new KUi.Pick() {
            @Override public void pick(int i) { p.reject(true, CANNED[i]); }
        });
    }

    private void toggleMute() {
        KeitaiInCallService s = KeitaiInCallService.instance();
        CallAudioState a = KeitaiInCallService.audio();
        if (s != null && a != null) s.setMuted(!a.isMuted());
    }

    private void toggleSpeaker() {
        KeitaiInCallService s = KeitaiInCallService.instance();
        CallAudioState a = KeitaiInCallService.audio();
        if (s == null || a == null) return;
        s.setAudioRoute(a.getRoute() == CallAudioState.ROUTE_SPEAKER ? CallAudioState.ROUTE_WIRED_OR_EARPIECE : CallAudioState.ROUTE_SPEAKER);
    }

    private void toggleHold(Call p) {
        if (p.getState() == Call.STATE_HOLDING) p.unhold();
        else if (p.getDetails().can(Call.Details.CAPABILITY_HOLD)) p.hold();
        else KUi.toast(this, "Hold is not available");
    }

    private Call other(Call p, int state) {
        for (Call c : KeitaiInCallService.calls()) if (c != p && c.getParent() == null && c.getState() == state) return c;
        return null;
    }

    private void menu(final Call p) {
        final ArrayList<String> labels = new ArrayList<String>();
        final ArrayList<String> ids = new ArrayList<String>();
        CallAudioState a = KeitaiInCallService.audio();
        labels.add(a != null && a.isMuted() ? "Unmute" : "Mute"); ids.add("mute");
        labels.add(a != null && a.getRoute() == CallAudioState.ROUTE_SPEAKER ? "Speaker off" : "Speaker on"); ids.add("speaker");
        labels.add(p.getState() == Call.STATE_HOLDING ? "Resume" : "Hold"); ids.add("hold");
        labels.add("Add call"); ids.add("add");
        final Call held = other(p, Call.STATE_HOLDING);
        if (held != null) { labels.add("Swap calls"); ids.add("swap"); }
        if (held != null && p.getDetails().can(Call.Details.CAPABILITY_MERGE_CONFERENCE)) { labels.add("Merge calls"); ids.add("merge"); }
        if (held != null && p.getDetails().can(Call.Details.CAPABILITY_SWAP_CONFERENCE)) { labels.add("Swap conference"); ids.add("swapconf"); }
        if (a != null && (a.getSupportedRouteMask() & CallAudioState.ROUTE_BLUETOOTH) != 0) {
            labels.add(a.getRoute() == CallAudioState.ROUTE_BLUETOOTH ? "Phone earpiece" : "Bluetooth"); ids.add("bt");
        }
        labels.add("Hang up"); ids.add("hangup");
        KUi.menu(this, "Call menu", labels.toArray(new String[0]), new KUi.Pick() {
            @Override public void pick(int i) {
                String id = ids.get(i);
                if ("mute".equals(id)) toggleMute();
                else if ("speaker".equals(id)) toggleSpeaker();
                else if ("hold".equals(id)) toggleHold(p);
                else if ("add".equals(id)) startActivity(new Intent(InCallActivity.this, DialerActivity.class).putExtra("org.kyf37.dialer.ADD_CALL", true));
                else if ("swap".equals(id) && held != null) { if (p.getState() == Call.STATE_ACTIVE) p.hold(); held.unhold(); }
                else if ("merge".equals(id)) p.mergeConference();
                else if ("swapconf".equals(id)) p.swapConference();
                else if ("bt".equals(id)) {
                    KeitaiInCallService s = KeitaiInCallService.instance();
                    CallAudioState au = KeitaiInCallService.audio();
                    if (s != null && au != null) s.setAudioRoute(au.getRoute() == CallAudioState.ROUTE_BLUETOOTH
                            ? CallAudioState.ROUTE_WIRED_OR_EARPIECE : CallAudioState.ROUTE_BLUETOOTH);
                }
                else if ("hangup".equals(id)) p.disconnect();
            }
        });
    }

    private void chooseLine(final Call p) {
        TelecomManager tm = (TelecomManager) getSystemService(TELECOM_SERVICE);
        final List<PhoneAccountHandle> accounts;
        try { accounts = tm.getCallCapablePhoneAccounts(); } catch (SecurityException e) { p.disconnect(); return; }
        if (accounts == null || accounts.isEmpty()) { p.disconnect(); return; }
        String[] labels = new String[accounts.size()];
        for (int i = 0; i < labels.length; i++) {
            android.telecom.PhoneAccount pa = tm.getPhoneAccount(accounts.get(i));
            labels[i] = pa != null && pa.getLabel() != null ? pa.getLabel().toString() : accounts.get(i).getId();
        }
        KUi.menu(this, "Call with", labels, new KUi.Pick() {
            @Override public void pick(int i) { p.phoneAccountSelected(accounts.get(i), false); }
        });
    }

    // ------------------------------------------------------------------------------------------ keys

    private static char dtmfChar(int code) {
        if (code == KeyEvent.KEYCODE_STAR) return '*';
        if (code == KeyEvent.KEYCODE_POUND) return '#';
        int d = KUi.digit(code);
        return d >= 0 ? (char) ('0' + d) : 0;
    }

    @Override public boolean onKeyDown(int code, KeyEvent ev) {
        Call p = KeitaiInCallService.primary();
        if (p == null) {
            if (code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_ENDCALL || code == KeyEvent.KEYCODE_CALL) { finish(); return true; }
            return super.onKeyDown(code, ev);
        }
        int st = p.getState();
        char dc = dtmfChar(code);
        if (dc != 0 && st == Call.STATE_ACTIVE) {
            if (ev.getRepeatCount() == 0) {
                p.playDtmfTone(dc);
                dtmfText.append(dc);
                if (dtmfText.length() > 24) dtmfText.delete(0, dtmfText.length() - 24);
                dtmf.setText(dtmfText.toString());
                lastKey = code;
            }
            return true;
        }
        if (ev.getRepeatCount() != 0) return super.onKeyDown(code, ev);
        if (st == Call.STATE_RINGING) {
            if (code == KeyEvent.KEYCODE_CALL || code == KeyEvent.KEYCODE_DPAD_CENTER || code == KeyEvent.KEYCODE_ENTER) { answer(p); return true; }
            if (code == KeyEvent.KEYCODE_ENDCALL || code == KeyEvent.KEYCODE_BACK) { p.reject(false, null); return true; }
            if (KUi.isMenuKey(code)) { rejectWithText(p); return true; }
            return true; // nothing else may leak through while ringing
        }
        if (st == Call.STATE_SELECT_PHONE_ACCOUNT) {
            if (code == KeyEvent.KEYCODE_DPAD_CENTER || code == KeyEvent.KEYCODE_ENTER || code == KeyEvent.KEYCODE_CALL) { chooseLine(p); return true; }
            if (code == KeyEvent.KEYCODE_ENDCALL || code == KeyEvent.KEYCODE_BACK) { p.disconnect(); return true; }
            return true;
        }
        if (st == Call.STATE_DISCONNECTED) {
            if (code == KeyEvent.KEYCODE_ENDCALL || code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_DPAD_CENTER) { finish(); return true; }
            return true;
        }
        switch (code) {
            case KeyEvent.KEYCODE_ENDCALL: p.disconnect(); return true;
            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER:
                if (st == Call.STATE_HOLDING) toggleHold(p); else toggleMute();
                return true;
            case KeyEvent.KEYCODE_DPAD_UP: toggleSpeaker(); return true;
            case KeyEvent.KEYCODE_DPAD_DOWN: toggleHold(p); return true;
            case KeyEvent.KEYCODE_CALL: {
                Call held = other(p, Call.STATE_HOLDING);
                if (held != null) { if (st == Call.STATE_ACTIVE) p.hold(); held.unhold(); }
                else startActivity(new Intent(this, DialerActivity.class).putExtra("org.kyf37.dialer.ADD_CALL", true));
                return true; }
            case KeyEvent.KEYCODE_BACK: moveTaskToBack(true); return true;
            default: break;
        }
        if (KUi.isMenuKey(code)) { menu(p); return true; }
        return super.onKeyDown(code, ev);
    }

    @Override public boolean onKeyUp(int code, KeyEvent ev) {
        char dc = dtmfChar(code);
        if (dc != 0) {
            Call p = KeitaiInCallService.primary();
            if (p != null && p.getState() == Call.STATE_ACTIVE) p.stopDtmfTone();
            return true;
        }
        return super.onKeyUp(code, ev);
    }

    @Override public void onBackPressed() {
        // Back (Clear) never closes an active call screen; onKeyDown handles the cases above.
        if (!KeitaiInCallService.hasCalls()) finish(); else moveTaskToBack(true);
    }
}
