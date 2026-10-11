package org.kyf37.subdisplay;

import android.app.Notification;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

/** Feeds new notifications to the outer screen (OuterScreenService.onNotification). Enabled by OuterScreenService itself. */
public final class NotifListener extends NotificationListenerService {
    static boolean interesting(StatusBarNotification s) {
        Notification n = s.getNotification();
        if (n == null) return false;
        if ((n.flags & (Notification.FLAG_ONGOING_EVENT | Notification.FLAG_FOREGROUND_SERVICE | Notification.FLAG_GROUP_SUMMARY)) != 0) return false;
        if (Notification.CATEGORY_CALL.equals(n.category) || Notification.CATEGORY_TRANSPORT.equals(n.category)
                || Notification.CATEGORY_PROGRESS.equals(n.category) || Notification.CATEGORY_SERVICE.equals(n.category)) return false;
        String pkg = s.getPackageName();
        return !("android".equals(pkg) || "com.android.systemui".equals(pkg));
    }

    private int count() {
        int c = 0;
        try {
            StatusBarNotification[] all = getActiveNotifications();
            if (all != null) for (StatusBarNotification s : all) if (interesting(s)) c++;
        } catch (RuntimeException ignored) { }
        return c;
    }

    @Override public void onListenerConnected() {
        OuterScreenService svc = OuterScreenService.instance;
        if (svc != null) svc.onUnread(count());
    }

    @Override public void onNotificationPosted(StatusBarNotification s) {
        OuterScreenService svc = OuterScreenService.instance;
        if (svc == null) return;
        int unread = count();
        if (!interesting(s)) { svc.onUnread(unread); return; }
        Notification n = s.getNotification();
        CharSequence title = n.extras.getCharSequence(Notification.EXTRA_TITLE);
        CharSequence text = n.extras.getCharSequence(Notification.EXTRA_TEXT);
        if (text == null) text = n.extras.getCharSequence(Notification.EXTRA_BIG_TEXT);
        String t = title == null ? "" : title.toString();
        String b = text == null ? "" : text.toString();
        if (t.isEmpty() && b.isEmpty()) { svc.onUnread(unread); return; }
        String pkg = s.getPackageName();
        boolean message = Notification.CATEGORY_MESSAGE.equals(n.category) || Notification.CATEGORY_EMAIL.equals(n.category)
                || pkg.contains("messag") || pkg.contains("sms") || pkg.contains("mail");
        svc.onNotification(s.getKey(), t, b, message, unread);
    }

    @Override public void onNotificationRemoved(StatusBarNotification s) {
        OuterScreenService svc = OuterScreenService.instance;
        if (svc != null) svc.onUnread(count());
    }
}
