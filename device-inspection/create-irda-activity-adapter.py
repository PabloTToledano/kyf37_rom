from pathlib import Path
r=Path('/home/pablo/kyf37-rom/irda-compat')
p=r/'src/jp/kyocera/kcfp/app/KCfpActivityManagerUtil.java'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text('''package jp.kyocera.kcfp.app;
import android.app.*;
import android.content.*;
import android.os.Bundle;
import java.util.WeakHashMap;
/** Preserve original per-activity End key behavior using the protected KYF37 policy broadcast. */
public final class KCfpActivityManagerUtil {
 private static final WeakHashMap<Activity,Entry> entries=new WeakHashMap<Activity,Entry>();
 private static boolean registered;
 private static final class Entry extends BroadcastReceiver {
  final Activity activity;int mode;String message;
  Entry(Activity a){activity=a;}
  public void onReceive(Context c,Intent i){
   if(!activity.hasWindowFocus() || activity.isFinishing())return;
   if(mode>=2)new AlertDialog.Builder(activity).setMessage(message==null?"End this transfer?":message)
     .setPositiveButton(android.R.string.ok,new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int w){finish();}}).setNegativeButton(android.R.string.cancel,null).show();
   else finish();
  }
  void finish(){if(mode==1 || mode==3)activity.moveTaskToBack(true);else activity.finish();}
 }
 public static synchronized void resetEndKeyBehavior(Activity a){setEndKeyBehavior(a,0,null);}
 public static synchronized void setEndKeyBehavior(Activity a,int mode){setEndKeyBehavior(a,mode,null);}
 public static synchronized void setEndKeyBehavior(Activity a,int mode,String message){
  if(a==null)throw new NullPointerException("activity is null");
  Entry e=entries.get(a);
  if(e==null){e=new Entry(a);entries.put(a,e);a.registerReceiver(e,new IntentFilter("org.kyf37.END_CALL"));}
  e.mode=mode>=0 && mode<=3?mode:0;e.message=message;
  if(!registered){registered=true;a.getApplication().registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks(){
   public void onActivityDestroyed(Activity x){Entry item=entries.remove(x);if(item!=null)x.unregisterReceiver(item);}
   public void onActivityCreated(Activity x,Bundle b){}public void onActivityStarted(Activity x){}
   public void onActivityResumed(Activity x){}public void onActivityPaused(Activity x){}
   public void onActivityStopped(Activity x){}public void onActivitySaveInstanceState(Activity x,Bundle b){}
  });}
 }
}
''')
print('Actual foreground End-key handling adapter written')

