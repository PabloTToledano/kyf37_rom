// KYF37 GPS test tool. Run: app_process -Djava.class.path=/data/local/tmp/gpstest.jar /system/bin GpsTest [seconds]
import android.content.Context;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Looper;
import java.lang.reflect.Method;

public class GpsTest {
    public static void main(String[] args) throws Exception {
        final int secs = args.length > 0 ? Integer.parseInt(args[0]) : 60;
        Looper.prepareMainLooper();
        Class<?> at = Class.forName("android.app.ActivityThread");
        Method sm = at.getMethod("systemMain");
        Object thread = sm.invoke(null);
        Context sys = (Context) at.getMethod("getSystemContext").invoke(thread);
        Context ctx = sys.createPackageContext("com.android.shell", 0);
        final LocationManager lm = (LocationManager) ctx.getSystemService(Context.LOCATION_SERVICE);
        System.out.println("providers: " + lm.getAllProviders() + " gps enabled=" + lm.isProviderEnabled("gps"));
        lm.registerGnssStatusCallback(new GnssStatus.Callback() {
            public void onStarted() { System.out.println("GNSS engine STARTED"); }
            public void onStopped() { System.out.println("GNSS engine STOPPED"); }
            public void onFirstFix(int ttffMillis) { System.out.println("FIRST FIX ttff=" + ttffMillis + "ms"); }
            public void onSatelliteStatusChanged(GnssStatus s) {
                int used = 0; for (int i = 0; i < s.getSatelliteCount(); i++) if (s.usedInFix(i)) used++;
                System.out.println("satellites visible=" + s.getSatelliteCount() + " usedInFix=" + used);
            }
        });
        lm.requestLocationUpdates("gps", 1000, 0, new LocationListener() {
            public void onLocationChanged(Location l) { System.out.println("LOCATION " + l.getLatitude() + "," + l.getLongitude() + " acc=" + l.getAccuracy()); }
            public void onStatusChanged(String p, int st, Bundle e) { System.out.println("status " + p + " " + st); }
            public void onProviderEnabled(String p) { System.out.println("enabled " + p); }
            public void onProviderDisabled(String p) { System.out.println("disabled " + p); }
        }, Looper.getMainLooper());
        new Thread(new Runnable() { public void run() { try { Thread.sleep(secs * 1000L); } catch (Exception e) {} System.out.println("done"); System.exit(0); } }).start();
        Looper.loop();
    }
}
