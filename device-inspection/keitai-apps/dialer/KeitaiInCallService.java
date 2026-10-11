package org.kyf37.dialer;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.telecom.Call;
import android.telecom.CallAudioState;
import android.telecom.InCallService;
import java.util.ArrayList;
import java.util.List;

/**
 * Telecom binds this service when org.kyf37.dialer is the default dialer. It keeps the live call list for
 * {@link InCallActivity}, raises the incoming-call screen (full-screen intent notification plus a direct start)
 * and keeps an ongoing-call notification. Telecom itself plays the ringtone and writes the call log.
 */
public class KeitaiInCallService extends InCallService {
    static final int NOTIF_ID = 4701;
    static final String CH_INCOMING = "incoming_call";
    static final String CH_ONGOING = "ongoing_call";
    static final String ACTION_ANSWER = "org.kyf37.dialer.ANSWER";
    static final String ACTION_DECLINE = "org.kyf37.dialer.DECLINE";
    static final String ACTION_HANGUP = "org.kyf37.dialer.HANGUP";

    public interface Listener { void onCallsChanged(); }

    private static final ArrayList<Call> CALLS = new ArrayList<Call>();
    private static final ArrayList<Listener> LISTENERS = new ArrayList<Listener>();
    private static KeitaiInCallService sInstance;
    private static CallAudioState sAudio;

    private final Call.Callback callback = new Call.Callback() {
        @Override public void onStateChanged(Call call, int state) { changed(); }
        @Override public void onDetailsChanged(Call call, Call.Details d) { changed(); }
        @Override public void onChildrenChanged(Call call, List<Call> children) { changed(); }
        @Override public void onParentChanged(Call call, Call parent) { changed(); }
        @Override public void onConferenceableCallsChanged(Call call, List<Call> calls) { changed(); }
        @Override public void onCallDestroyed(Call call) { changed(); }
    };

    // ------------------------------------------------------------------------------------------ static state

    public static synchronized boolean hasCalls() { return !CALLS.isEmpty(); }
    public static synchronized List<Call> calls() { return new ArrayList<Call>(CALLS); }
    public static synchronized CallAudioState audio() { return sAudio; }
    public static synchronized KeitaiInCallService instance() { return sInstance; }
    public static synchronized void addListener(Listener l) { if (!LISTENERS.contains(l)) LISTENERS.add(l); }
    public static synchronized void removeListener(Listener l) { LISTENERS.remove(l); }

    /** The call the user should deal with first: ringing, then dialing/active, then held. */
    public static synchronized Call primary() {
        Call best = null;
        for (Call c : CALLS) {
            if (c.getParent() != null) continue;
            if (rank(c) < (best == null ? 99 : rank(best))) best = c;
        }
        return best;
    }

    static int rank(Call c) {
        switch (c.getState()) {
            case Call.STATE_RINGING: return 0;
            case Call.STATE_SELECT_PHONE_ACCOUNT: return 1;
            case Call.STATE_DIALING:
            case Call.STATE_CONNECTING:
            case Call.STATE_ACTIVE: return 2;
            case Call.STATE_HOLDING: return 3;
            case Call.STATE_DISCONNECTING:
            case Call.STATE_DISCONNECTED: return 4;
            default: return 5;
        }
    }

    // ------------------------------------------------------------------------------------------ service

    @Override public void onCreate() {
        super.onCreate();
        synchronized (KeitaiInCallService.class) { sInstance = this; }
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        NotificationChannel in = new NotificationChannel(CH_INCOMING, "Incoming calls", NotificationManager.IMPORTANCE_HIGH);
        in.setSound(null, null); // Telecom plays the ringtone
        in.enableVibration(false);
        in.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(in);
        NotificationChannel on = new NotificationChannel(CH_ONGOING, "Ongoing calls", NotificationManager.IMPORTANCE_LOW);
        on.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(on);
    }

    @Override public void onDestroy() {
        synchronized (KeitaiInCallService.class) { if (sInstance == this) sInstance = null; CALLS.clear(); }
        ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).cancel(NOTIF_ID);
        super.onDestroy();
    }

    @Override public void onCallAdded(Call call) {
        call.registerCallback(callback);
        synchronized (KeitaiInCallService.class) { CALLS.add(call); }
        changed();
        showUi();
    }

    @Override public void onCallRemoved(Call call) {
        call.unregisterCallback(callback);
        synchronized (KeitaiInCallService.class) { CALLS.remove(call); }
        changed();
    }

    @Override public void onCallAudioStateChanged(CallAudioState state) {
        synchronized (KeitaiInCallService.class) { sAudio = state; }
        changed();
    }

    @Override public void onBringToForeground(boolean showDialpad) { showUi(); }

    // ------------------------------------------------------------------------------------------ UI plumbing

    private void showUi() {
        Intent i = new Intent(this, InCallActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try {
            startActivity(i);
        } catch (RuntimeException e) {
            // Background activity start can be refused: the full-screen notification covers that case.
        }
    }

    private void changed() {
        ArrayList<Listener> copy;
        synchronized (KeitaiInCallService.class) { copy = new ArrayList<Listener>(LISTENERS); }
        for (Listener l : copy) l.onCallsChanged();
        updateNotification();
    }

    private PendingIntent broadcast(String action, int req) {
        Intent i = new Intent(action).setPackage(getPackageName());
        return PendingIntent.getBroadcast(this, req, i, PendingIntent.FLAG_UPDATE_CURRENT);
    }

    private void updateNotification() {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        Call p = primary();
        if (p == null) { nm.cancel(NOTIF_ID); return; }
        String who = CallUi.displayName(this, p);
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, InCallActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP), PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b;
        if (p.getState() == Call.STATE_RINGING) {
            b = new Notification.Builder(this, CH_INCOMING)
                    .setContentTitle("Incoming call")
                    .setContentText(who)
                    .setSmallIcon(android.R.drawable.sym_action_call)
                    .setCategory(Notification.CATEGORY_CALL)
                    .setOngoing(true)
                    .setContentIntent(open)
                    .setFullScreenIntent(open, true)
                    .addAction(new Notification.Action.Builder(null, "Answer", broadcast(ACTION_ANSWER, 1)).build())
                    .addAction(new Notification.Action.Builder(null, "Decline", broadcast(ACTION_DECLINE, 2)).build());
        } else {
            b = new Notification.Builder(this, CH_ONGOING)
                    .setContentTitle(p.getState() == Call.STATE_HOLDING ? "Call on hold" : "Ongoing call")
                    .setContentText(who)
                    .setSmallIcon(android.R.drawable.sym_action_call)
                    .setCategory(Notification.CATEGORY_CALL)
                    .setOngoing(true)
                    .setUsesChronometer(p.getDetails().getConnectTimeMillis() > 0)
                    .setWhen(p.getDetails().getConnectTimeMillis() > 0 ? p.getDetails().getConnectTimeMillis() : System.currentTimeMillis())
                    .setContentIntent(open)
                    .addAction(new Notification.Action.Builder(null, "Hang up", broadcast(ACTION_HANGUP, 3)).build());
        }
        nm.notify(NOTIF_ID, b.build());
    }

    /** Notification buttons. */
    public static final class ActionReceiver extends android.content.BroadcastReceiver {
        @Override public void onReceive(Context c, Intent i) {
            Call p = primary();
            if (p == null || i.getAction() == null) return;
            switch (i.getAction()) {
                case ACTION_ANSWER: p.answer(android.telecom.VideoProfile.STATE_AUDIO_ONLY); break;
                case ACTION_DECLINE: p.reject(false, null); break;
                case ACTION_HANGUP: p.disconnect(); break;
                default: break;
            }
        }
    }
}
