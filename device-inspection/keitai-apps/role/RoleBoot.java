package @PKG@;

import android.app.role.RoleManager;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Process;
import java.util.List;

/**
 * Makes this app the holder of its default role (meta-data org.kyf37.ROLE, e.g. android.app.role.DIALER) once per
 * ROM build. Needed because RoleManager only applies config_defaultDialer / config_defaultSms when a role has no holder:
 * a phone that is updated with its data kept would stay with the old (Lineage) app. A later choice in
 * Settings > Apps > Default apps sticks until the next ROM build (fingerprint) changes.
 */
public final class RoleBoot extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        try {
            PackageManager pm = c.getPackageManager();
            android.os.Bundle meta = pm.getReceiverInfo(new ComponentName(c, RoleBoot.class), PackageManager.GET_META_DATA).metaData;
            String role = meta == null ? null : meta.getString("org.kyf37.ROLE");
            if (role == null) return;
            SharedPreferences sp = c.getSharedPreferences("role_boot", Context.MODE_PRIVATE);
            if (Build.FINGERPRINT.equals(sp.getString("fingerprint", ""))) return;
            RoleManager rm = (RoleManager) c.getSystemService(Context.ROLE_SERVICE);
            if (rm == null || !rm.isRoleAvailable(role)) return;
            List<String> holders = rm.getRoleHolders(role);
            sp.edit().putString("fingerprint", Build.FINGERPRINT).apply();
            if (holders != null && holders.contains(c.getPackageName())) return;
            rm.addRoleHolderAsUser(role, c.getPackageName(), 0, Process.myUserHandle(), c.getMainExecutor(), new java.util.function.Consumer<Boolean>() {
                @Override public void accept(Boolean ok) {
                    android.util.Log.i("Kyf37RoleBoot", "role " + role + " -> " + c.getPackageName() + ": " + ok);
                }
            });
        } catch (Throwable t) {
            android.util.Log.w("Kyf37RoleBoot", "role setup failed", t);
        }
    }
}
