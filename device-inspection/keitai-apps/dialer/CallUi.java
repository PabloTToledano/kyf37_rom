package org.kyf37.dialer;

import android.content.Context;
import android.net.Uri;
import android.telecom.Call;
import android.telecom.DisconnectCause;

/** Small helpers shared by the in-call screen and the notification. */
final class CallUi {
    private CallUi() { }

    static String number(Call c) {
        Call.Details d = c.getDetails();
        Uri h = d == null ? null : d.getHandle();
        if (h == null) return "";
        String s = h.getSchemeSpecificPart();
        if (s == null) return "";
        int semi = s.indexOf(';');
        if (semi > 0) s = s.substring(0, semi);
        return Uri.decode(s);
    }

    static String displayName(Context ctx, Call c) {
        Call.Details d = c.getDetails();
        if (d != null && d.getHandle() != null && "voicemail".equals(d.getHandle().getScheme())) return "Voicemail";
        String num = number(c);
        String nm = KUi.nameFor(ctx, num);
        if (nm != null && nm.length() > 0) return nm;
        if (d != null && d.getCallerDisplayName() != null && d.getCallerDisplayName().length() > 0) return d.getCallerDisplayName();
        if (num.length() > 0) return num;
        return "Unknown";
    }

    static String stateText(Call c) {
        switch (c.getState()) {
            case Call.STATE_RINGING: return "Incoming call";
            case Call.STATE_DIALING: return "Calling...";
            case Call.STATE_CONNECTING: return "Connecting...";
            case Call.STATE_ACTIVE: return "";
            case Call.STATE_HOLDING: return "On hold";
            case Call.STATE_DISCONNECTING: return "Ending...";
            case Call.STATE_DISCONNECTED: return disconnectText(c);
            case Call.STATE_SELECT_PHONE_ACCOUNT: return "Choose a line";
            default: return "";
        }
    }

    static String disconnectText(Call c) {
        DisconnectCause cause = c.getDetails().getDisconnectCause();
        if (cause == null) return "Call ended";
        switch (cause.getCode()) {
            case DisconnectCause.BUSY: return "Busy";
            case DisconnectCause.REJECTED: return "Call rejected";
            case DisconnectCause.MISSED: return "Missed call";
            case DisconnectCause.REMOTE: return "Call ended";
            case DisconnectCause.LOCAL: return "Call ended";
            case DisconnectCause.ERROR: return "Call failed";
            case DisconnectCause.RESTRICTED: return "Calling is restricted";
            case DisconnectCause.CANCELED: return "Call cancelled";
            default: return "Call ended";
        }
    }
}
