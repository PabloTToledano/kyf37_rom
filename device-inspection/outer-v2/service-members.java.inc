    // KYF37_OUTER_V2: Java-rendered clock + call/notification alerts on the outer panel
    static volatile OuterScreenService instance;
    private static final class Alert {
        int kind;
        String title, body;
        long start, until;
    }
    private Alert alert;
    private int alertTick;
    private int unread;
    private int callState = android.telephony.TelephonyManager.CALL_STATE_IDLE;
    private long callStart;
    private boolean callAnswered;
    private String callName = "", callNumber = "";
    private PowerManager.WakeLock alertLock;
    private final java.util.HashMap<String, String> shown = new java.util.HashMap<String, String>();
    private final Runnable alertRun = new Runnable() { public void run() {
        if (alert == null) return;
        if (!closed()) { clearAlert(); refresh(); return; }
        long now = SystemClock.elapsedRealtime();
        if (now >= alert.until) { clearAlert(); light(); refresh(); return; }
        String title = alert.title, body = alert.body;
        int remaining = alert.until == Long.MAX_VALUE ? 100 : (int) (100 * (alert.until - now) / Math.max(1, alert.until - alert.start));
        if (alert.kind == OuterUi.K_INCALL) {
            long s = (now - callStart) / 1000;
            body = String.format("%d:%02d", s / 60, s % 60);
        }
        if (updateVideo(OuterUi.pack(OuterUi.alert(alert.kind, title, body, alertTick++, remaining))) != 0) { clearAlert(); refresh(); return; }
        handler.postDelayed(this, 100);
    } };
    private void showAlert(int kind, String title, String body, long durationMs) {
        if (!closed()) return;
        stopAnimation(); stopMovie(); alarms.cancel(tick);
        Alert a = new Alert();
        a.kind = kind; a.title = title; a.body = body;
        a.start = SystemClock.elapsedRealtime();
        a.until = durationMs <= 0 ? Long.MAX_VALUE : a.start + durationMs;
        alert = a; alertTick = 0; blanked = false;
        if (alertLock == null) alertLock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "KYF37:OuterAlert");
        if (alertLock.isHeld()) alertLock.release();
        alertLock.acquire(durationMs <= 0 ? 600000 : durationMs + 2000);
        handler.removeCallbacks(alertRun);
        handler.post(alertRun);
    }
    private void clearAlert() {
        alert = null;
        handler.removeCallbacks(alertRun);
        if (alertLock != null && alertLock.isHeld()) alertLock.release();
    }
    /** Called by NotifListener on the binder thread. */
    void onNotification(final String key, final String title, final String body, final boolean message, final int count) {
        handler.post(new Runnable() { public void run() {
            unread = count;
            String sig = title + "\u0001" + body;
            if (sig.equals(shown.get(key))) { refresh(); return; }
            shown.put(key, sig);
            if (shown.size() > 64) shown.clear();
            if (callState == android.telephony.TelephonyManager.CALL_STATE_RINGING) return;
            int ms = 7000 + Math.min(8000, 100 * (title.length() + body.length()));
            showAlert(message ? OuterUi.K_MESSAGE : OuterUi.K_NOTIF, title.isEmpty() ? body : title, title.isEmpty() ? "" : body, ms);
            if (alert == null) refresh();
        } });
    }
    void onUnread(final int count) {
        handler.post(new Runnable() { public void run() { unread = count; if (alert == null) refresh(); } });
    }
    private String lookupName(String number) {
        if (number == null || number.isEmpty()) return "";
        try {
            android.net.Uri uri = android.net.Uri.withAppendedPath(android.provider.ContactsContract.PhoneLookup.CONTENT_FILTER_URI, android.net.Uri.encode(number));
            android.database.Cursor c = getContentResolver().query(uri, new String[] { android.provider.ContactsContract.PhoneLookup.DISPLAY_NAME }, null, null, null);
            if (c != null) try { if (c.moveToFirst()) return c.getString(0); } finally { c.close(); }
        } catch (RuntimeException e) { Log.w("KYF37OuterScreen", "Caller lookup failed", e); }
        return "";
    }
    private final android.telephony.PhoneStateListener phoneListener = new android.telephony.PhoneStateListener() {
        @Override public void onCallStateChanged(int state, String number) {
            int old = callState;
            callState = state;
            if (state == android.telephony.TelephonyManager.CALL_STATE_RINGING) {
                callNumber = number == null ? "" : number;
                callName = lookupName(callNumber);
                callAnswered = false;
                showCallAlert();
            } else if (state == android.telephony.TelephonyManager.CALL_STATE_OFFHOOK) {
                if (old == android.telephony.TelephonyManager.CALL_STATE_RINGING) callAnswered = true;
                callStart = SystemClock.elapsedRealtime();
                showCallAlert();
            } else if (old == android.telephony.TelephonyManager.CALL_STATE_RINGING && !callAnswered) {
                clearAlert();
                showAlert(OuterUi.K_MISSED, "Missed call", callName.isEmpty() ? (callNumber.isEmpty() ? "Unknown" : callNumber) : callName, 12000);
                if (alert == null) refresh();
            } else {
                clearAlert(); light(); refresh();
            }
        }
    };
    private void showCallAlert() {
        if (!closed()) return;
        String who = !callName.isEmpty() ? callName : (!callNumber.isEmpty() ? callNumber : "Unknown");
        if (callState == android.telephony.TelephonyManager.CALL_STATE_RINGING)
            showAlert(OuterUi.K_RING, who, !callName.isEmpty() && !callNumber.isEmpty() ? callNumber : "Incoming call", 0);
        else if (callState == android.telephony.TelephonyManager.CALL_STATE_OFFHOOK)
            showAlert(OuterUi.K_INCALL, who, "0:00", 0);
    }
    private String dateText(boolean longForm) {
        return new java.text.SimpleDateFormat(longForm ? "EEE d MMM" : "EEE d", java.util.Locale.getDefault()).format(new java.util.Date()).toUpperCase(java.util.Locale.getDefault());
    }
    /** frame -1 = idle (arg = phase); else scene animation frame (arg = scene). Composes the Java clock with the native mascot/actor layer. */
    private int drawFrame(int frame, Calendar now, int arg) {
        boolean mascotOn = animationOn();
        byte[] layer = renderLayer(frame, arg, arg);
        if (layer == null || layer.length != OuterUi.W * OuterUi.H) layer = new byte[OuterUi.W * OuterUi.H];
        byte[] clk = OuterUi.clock(now.get(Calendar.HOUR_OF_DAY), now.get(Calendar.MINUTE), now.get(Calendar.SECOND),
            cfg("kyf37_outer_clock_size", 2), cfg("kyf37_outer_time_format", 0) != 0, secondsOn(), cfg("kyf37_outer_battery", 3),
            battery, unread, dateText(true), dateText(false), mascotOn);
        int offset = 0;
        if (frame >= 0 && frame < 8) offset = -frame * 128 / 7;
        else if (frame >= 8 && frame < 28) offset = -128;
        else if (frame >= 28) { int t = frame - 28; offset = t < 16 ? -128 + t * 128 / 15 : 0; }
        int limit = mascotOn ? 96 : 128;
        for (int y = 0; y < OuterUi.H; y++) for (int x = 0; x < limit; x++) {
            if (clk[y * OuterUi.W + x] == 0) continue;
            int dx = x + offset;
            if (dx >= 0 && dx < OuterUi.W) layer[y * OuterUi.W + dx] = 1;
        }
        return updateVideo(OuterUi.pack(layer));
    }
    /** Root/system only (service is not exported): am startservice -a org.kyf37.action.OUTER_DEBUG_ALERT --ei kind N --es title T --es body B */
    private void debugAlert(Intent i) {
        showAlert(i.getIntExtra("kind", 0), i.getStringExtra("title"), i.getStringExtra("body"), i.getIntExtra("ms", 10000));
    }
    private void enableNotificationListener() {
        try {
            android.app.NotificationManager nm = (android.app.NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            ComponentName cn = new ComponentName(this, NotifListener.class);
            boolean had = nm.isNotificationListenerAccessGranted(cn);
            if (!had) nm.setNotificationListenerAccessGranted(cn, true);
            Log.i("KYF37OuterScreen", "notification listener granted before=" + had + " now=" + nm.isNotificationListenerAccessGranted(cn));
        } catch (Throwable t) { Log.w("KYF37OuterScreen", "Cannot enable notification listener", t); }
    }
