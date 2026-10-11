import android.app.Notification;
import android.app.INotificationManager;
import android.content.Context;
import android.os.ServiceManager;

/** Test helper (run as root via app_process): posts N notifications as package "android" on its existing channel.
 *  usage: app_process / Post <count> [prefix] */
public class Post {
    public static void main(String[] args) throws Exception {
        int n = args.length > 0 ? Integer.parseInt(args[0]) : 3;
        String prefix = args.length > 1 ? args[1] : "Walk";
        android.os.Looper.prepare();
        Object at = Class.forName("android.app.ActivityThread").getMethod("systemMain").invoke(null);
        Context ctx = (Context) at.getClass().getMethod("getSystemContext").invoke(at);
        INotificationManager nm = INotificationManager.Stub.asInterface(ServiceManager.getService("notification"));
        for (int i = 1; i <= n; i++) {
            Notification.Builder b = new Notification.Builder(ctx, "TrustInterface")
                .setSmallIcon(17301647).setContentTitle(prefix + " " + i)
                .setContentText("Body text number " + i + " for the keypad walk").setAutoCancel(true);
            nm.enqueueNotificationWithTag("android", "android", prefix + i, 9000 + i, b.build(), 0);
        }
        System.out.println("posted " + n);
        System.exit(0);
    }
}
