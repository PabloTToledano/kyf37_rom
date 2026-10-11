package org.kyf37.dialer;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.telecom.Connection;
import android.telecom.ConnectionRequest;
import android.telecom.ConnectionService;
import android.telecom.DisconnectCause;
import android.telecom.PhoneAccount;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;
import android.util.Log;

/**
 * DEBUG ONLY (ro.debuggable builds): a fake "KYF37 test line" so the real Telecom + in-call UI can be exercised on a
 * phone that has no radio. Nothing here is used on a production (user) build: the receiver ignores intents unless
 * Build.TYPE is not "user", and the account is only registered by that receiver.
 *   adb shell am broadcast -a org.kyf37.dialer.DEBUG_INCOMING --es number 600123456 -n org.kyf37.dialer/.TestConnectionService\$Debug
 *   adb shell am broadcast -a org.kyf37.dialer.DEBUG_OUTGOING --es number 600123456 -n ...
 *   adb shell am broadcast -a org.kyf37.dialer.DEBUG_REMOTE_HANGUP    (the other side ends the call)
 */
public class TestConnectionService extends ConnectionService {
    static final String TAG = "Kyf37TestLine";
    private static final Handler H = new Handler(Looper.getMainLooper());
    private static final java.util.ArrayList<TestConn> LIVE = new java.util.ArrayList<TestConn>();

    static PhoneAccountHandle handle(Context c) {
        return new PhoneAccountHandle(new ComponentName(c, TestConnectionService.class), "kyf37-test-line");
    }

    static void register(Context c) {
        PhoneAccount pa = PhoneAccount.builder(handle(c), "KYF37 test line")
                .setCapabilities(PhoneAccount.CAPABILITY_CALL_PROVIDER)
                .addSupportedUriScheme(PhoneAccount.SCHEME_TEL)
                .build();
        ((TelecomManager) c.getSystemService(Context.TELECOM_SERVICE)).registerPhoneAccount(pa);
    }

    static final class TestConn extends Connection {
        TestConn() {
            setConnectionCapabilities(CAPABILITY_HOLD | CAPABILITY_SUPPORT_HOLD | CAPABILITY_MUTE);
            synchronized (LIVE) { LIVE.add(this); }
        }
        void end(int cause) {
            setDisconnected(new DisconnectCause(cause));
            destroy();
            synchronized (LIVE) { LIVE.remove(this); }
        }
        @Override public void onAnswer() { setActive(); }
        @Override public void onAnswer(int videoState) { setActive(); }
        @Override public void onReject() { end(DisconnectCause.REJECTED); }
        @Override public void onReject(String msg) { Log.i(TAG, "rejected with message: " + msg); end(DisconnectCause.REJECTED); }
        @Override public void onDisconnect() { end(DisconnectCause.LOCAL); }
        @Override public void onAbort() { end(DisconnectCause.CANCELED); }
        @Override public void onHold() { setOnHold(); }
        @Override public void onUnhold() { setActive(); }
        @Override public void onPlayDtmfTone(char c) { Log.i(TAG, "DTMF down " + c); }
        @Override public void onStopDtmfTone() { Log.i(TAG, "DTMF up"); }
    }

    @Override public Connection onCreateOutgoingConnection(PhoneAccountHandle acct, ConnectionRequest req) {
        final TestConn c = new TestConn();
        c.setAddress(req.getAddress(), TelecomManager.PRESENTATION_ALLOWED);
        c.setDialing();
        H.postDelayed(new Runnable() { @Override public void run() { if (c.getState() == Connection.STATE_DIALING) c.setActive(); } }, 1500);
        return c;
    }

    @Override public Connection onCreateIncomingConnection(PhoneAccountHandle acct, ConnectionRequest req) {
        TestConn c = new TestConn();
        Uri addr = req.getAddress();
        if (addr == null && req.getExtras() != null) addr = req.getExtras().getParcelable(TelecomManager.EXTRA_INCOMING_CALL_ADDRESS);
        c.setAddress(addr, TelecomManager.PRESENTATION_ALLOWED);
        c.setRinging();
        return c;
    }

    /** Debug trigger. */
    public static class Debug extends BroadcastReceiver {
        @Override public void onReceive(Context ctx, Intent i) {
            if ("user".equals(Build.TYPE) || i.getAction() == null) return;
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            String number = i.getStringExtra("number");
            if (number == null) number = "600123456";
            register(ctx);
            try { doIt(ctx, tm, i, number); }
            catch (RuntimeException e) { Log.w(TAG, "debug action failed (enable the line: telecom set-phone-account-enabled org.kyf37.dialer/org.kyf37.dialer.TestConnectionService kyf37-test-line 0)", e); }
        }

        private void doIt(Context ctx, TelecomManager tm, Intent i, String number) {
            switch (i.getAction()) {
                case "org.kyf37.dialer.DEBUG_INCOMING": {
                    Bundle x = new Bundle();
                    x.putParcelable(TelecomManager.EXTRA_INCOMING_CALL_ADDRESS, Uri.fromParts("tel", number, null));
                    tm.addNewIncomingCall(handle(ctx), x);
                    break; }
                case "org.kyf37.dialer.DEBUG_OUTGOING": {
                    Bundle x = new Bundle();
                    x.putParcelable(TelecomManager.EXTRA_PHONE_ACCOUNT_HANDLE, handle(ctx));
                    tm.placeCall(Uri.fromParts("tel", number, null), x);
                    break; }
                case "org.kyf37.dialer.DEBUG_REMOTE_HANGUP": {
                    synchronized (LIVE) {
                        for (TestConn c : new java.util.ArrayList<TestConn>(LIVE)) c.end(DisconnectCause.REMOTE);
                    }
                    break; }
                default: break;
            }
        }
    }
}
