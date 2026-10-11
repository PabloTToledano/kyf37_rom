from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'packages/apps/Kyf37KeypadSettings'
(p/'src/org/kyf37/keypad').mkdir(parents=True,exist_ok=True)
(p/'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_PACKAGE_NAME := Kyf37KeypadSettings
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_CERTIFICATE := platform
LOCAL_PRIVILEGED_MODULE := true
LOCAL_PRIVATE_PLATFORM_APIS := true
include $(BUILD_PACKAGE)
''')
(p/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.keypad" android:sharedUserId="android.uid.system">
<uses-permission android:name="android.permission.WRITE_SECURE_SETTINGS"/>
<uses-permission android:name="android.permission.WRITE_SETTINGS"/>
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
<application android:label="Keypad settings" android:theme="@android:style/Theme.Material.Light" android:allowBackup="false">
<activity android:name=".KeypadSettings" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
<receiver android:name=".Boot" android:exported="false"><intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/></intent-filter></receiver>
</application></manifest>
''')
(p/'src/org/kyf37/keypad/Boot.java').write_text('''package org.kyf37.keypad;
import android.content.*;
import android.provider.Settings;
public final class Boot extends BroadcastReceiver {
 public void onReceive(Context c,Intent i) {
  Settings.System.putInt(c.getContentResolver(),"end_button_behavior",0);
  if(Settings.Secure.getInt(c.getContentResolver(),"kyf37_lid_only_sleep",1)!=0)
   Settings.System.putInt(c.getContentResolver(),"screen_off_timeout",Integer.MAX_VALUE);
 }
}
''')
(p/'src/org/kyf37/keypad/KeypadSettings.java').write_text('''package org.kyf37.keypad;
import android.app.*;
import android.os.Bundle;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import java.util.*;
public final class KeypadSettings extends Activity {
 private final int[] scans={59,60,61,62,63,64,65,355,231,116,254,103,108,105,106,28,11,2,3,4,5,6,7,8,9,10,55,253};
 private final int[] defaults={131,132,133,134,187,141,142,4,5,6,27,19,20,21,22,23,7,8,9,10,11,12,13,14,15,16,17,18};
 private final String[] names={"F1","F2","F3","F4","Extra key F5","Extra key F6","Extra key F7","Centre Clear / Back","Call","Hangup","Exterior side key","D-pad Up","D-pad Down","D-pad Left","D-pad Right","Select","0","1","2","3","4","5","6","7","8","9","Star","Hash"};
 private final int[] actions={0,4,3,82,133,187,23,19,20,21,22,24,25,5,6,27,131,132,134};
 private final String[] labels={"Default","Back","Home","Menu","Pointer toggle","Recent apps","Select","Up","Down","Left","Right","Volume up","Volume down","Call","Hangup","Camera","F1","F2","F4"};
 private ArrayAdapter<String> adapter;
 private ListView list;
 @Override public void onCreate(Bundle b) {
  super.onCreate(b);setTitle("Keypad settings");
  list=new ListView(this);list.setItemsCanFocus(false);
  adapter=new ArrayAdapter<String>(this,android.R.layout.simple_list_item_1,new ArrayList<String>());
  list.setAdapter(adapter);setContentView(list);
  list.setOnItemClickListener((parent,view,pos,id)->choose(pos));refresh();list.requestFocus();
 }
 private int get(String key,int fallback){return Settings.Secure.getInt(getContentResolver(),key,fallback);}
 private void refresh(){
  adapter.clear();
  adapter.add("Sleep only when lid closes: "+(get("kyf37_lid_only_sleep",1)!=0?"On":"Off"));
  adapter.add("Pointer speed: "+get("kyf37_pointer_step",12)+" pixels");
  adapter.add("Reset key mappings");
  for(int j=0;j<scans.length;j++){
   int action=get("kyf37_key_"+scans[j],defaults[j]);
   adapter.add(names[j]+" → "+KeyEvent.keyCodeToString(action).replace("KEYCODE_",""));
  }
  adapter.notifyDataSetChanged();
 }
 private void choose(int pos){
  if(pos==0){int value=get("kyf37_lid_only_sleep",1)==0?1:0;
   Settings.Secure.putInt(getContentResolver(),"kyf37_lid_only_sleep",value);
   Settings.System.putInt(getContentResolver(),"screen_off_timeout",value==1?Integer.MAX_VALUE:60000);
   refresh();return;
  }
  if(pos==1){new AlertDialog.Builder(this).setTitle("Pointer speed")
   .setItems(new String[]{"Fine: 6 pixels","Normal: 12 pixels","Fast: 24 pixels","Very fast: 36 pixels"},(d,n)->{
    Settings.Secure.putInt(getContentResolver(),"kyf37_pointer_step",new int[]{6,12,24,36}[n]);refresh();}).show();return;}
  if(pos==2){new AlertDialog.Builder(this).setTitle("Reset mappings?")
   .setMessage("Restore F3 pointer, F4 Home, Centre Clear Back and normal D-pad controls.")
   .setPositiveButton("Reset",(d,n)->{for(int scan:scans)Settings.Secure.putString(getContentResolver(),"kyf37_key_"+scan,null);refresh();})
   .setNegativeButton("Cancel",null).show();return;}
  final int j=pos-3;
  new AlertDialog.Builder(this).setTitle(names[j]).setItems(labels,(d,n)->{
   if(actions[n]==0)Settings.Secure.putString(getContentResolver(),"kyf37_key_"+scans[j],null);
   else Settings.Secure.putInt(getContentResolver(),"kyf37_key_"+scans[j],actions[n]);refresh();}).show();
 }
}
''')
p=root/'packages/apps/Settings/res/xml/top_level_settings.xml'
s=p.read_text()
if 'kyf37_keypad_settings' not in s:
 n=s.rfind('</PreferenceScreen>');assert n>0
 s=s[:n]+'''    <Preference android:key="kyf37_keypad_settings" android:title="Keypad settings" android:summary="Key actions, pointer speed and lid sleep">
        <intent android:targetPackage="org.kyf37.keypad" android:targetClass="org.kyf37.keypad.KeypadSettings" />
    </Preference>
'''+s[n:]
p.write_text(s)
p=root/'frameworks/base/services/core/java/com/android/server/policy/Kyf37Navigation.java'
s=p.read_text().replace('final int step = repeat > 8 ? 24 : 12;', '''final int configured = Math.max(4, Math.min(48, android.provider.Settings.Secure.getInt(
                            context.getContentResolver(), "kyf37_pointer_step", 12)));
                    final int step = repeat > 8 ? configured * 2 : configured;''')
p.write_text(s)
print('Built physical-key settings app and Settings entry; mappings and pointer speed wired to policy')
