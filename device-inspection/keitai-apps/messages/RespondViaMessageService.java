package org.kyf37.messages;

import android.app.IntentService;
import android.content.Intent;
import android.net.Uri;

/** Quick replies from the in-call screen ("Reject with message") and other apps: RESPOND_VIA_MESSAGE. */
public final class RespondViaMessageService extends IntentService {
    public RespondViaMessageService() { super("Kyf37RespondViaMessage"); }

    @Override protected void onHandleIntent(Intent i) {
        if (i == null || !"android.intent.action.RESPOND_VIA_MESSAGE".equals(i.getAction())) return;
        Uri d = i.getData();
        String text = i.getStringExtra(Intent.EXTRA_TEXT);
        if (d == null || text == null || text.length() == 0) return;
        String to = d.getSchemeSpecificPart();
        int q = to.indexOf('?');
        if (q >= 0) to = to.substring(0, q);
        for (String addr : to.split("[,;]")) {
            addr = Uri.decode(addr).trim();
            if (addr.length() > 0) Msgs.send(this, addr, text);
        }
    }
}
