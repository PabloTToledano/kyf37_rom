package org.kyf37.stockcompat;

import android.content.Context;
import android.os.Environment;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import android.telephony.PhoneNumberUtils;
import java.io.File;
import java.lang.reflect.Method;
import java.util.Locale;

/** Adapters to real Android 10 services. No fabricated storage or call state. */
public final class Kyf37StockAppCompat {
 private static Object cycleRule(Object policy) {
  try{return policy.getClass().getField("cycleRule").get(policy);}
  catch(Exception e){throw new IllegalStateException("Network cycle rule unavailable",e);}
 }
 public static int getCycleDay(Object policy) {
  Object rule=cycleRule(policy);
  try {
   if(rule==null||!Boolean.TRUE.equals(rule.getClass().getMethod("isMonthly").invoke(rule)))return -1;
   Object start=rule.getClass().getField("start").get(rule);
   return ((Integer)start.getClass().getMethod("getDayOfMonth").invoke(start)).intValue();
  } catch(Exception e){throw new IllegalStateException("Network cycle day unavailable",e);}
 }
 private static long cycleBoundary(long now,Object policy,boolean next) {
  int day=getCycleDay(policy);
  if(day==-1)throw new IllegalArgumentException("Unable to compute boundary without monthly cycle");
  Object rule=cycleRule(policy);
  try {
   Object start=rule.getClass().getField("start").get(rule);
   Object zone=start.getClass().getMethod("getZone").invoke(start);
   return Kyf37MonthlyCycle.boundary(now,day,zone.toString(),next);
  } catch(Exception e){throw new IllegalStateException("Network cycle timezone unavailable",e);}
 }
 public static long computeLastCycleBoundary(long now,Object policy){return cycleBoundary(now,policy,false);}
 public static long computeNextCycleBoundary(long now,Object policy){return cycleBoundary(now,policy,true);}
 public static void getPackageSizeInfo(final Object manager,final String packageName,final int user,final Object observer) {
  new Thread(new Runnable(){public void run(){
   Object legacy=null;boolean succeeded=false;
   try {
    Class<?> legacyType=Class.forName("android.content.pm.PackageStats");
    legacy=legacyType.getConstructor(String.class,int.class).newInstance(packageName,user);
    Object info=manager.getClass().getMethod("getApplicationInfoAsUser",String.class,int.class,int.class).invoke(manager,packageName,0,user);
    Object uuid=info.getClass().getField("storageUuid").get(info);
    Class<?> handleType=Class.forName("android.os.UserHandle");
    Object handle=handleType.getMethod("of",int.class).invoke(null,user);
    Object storage=context().getSystemService("storagestats");
    Object stats=storage.getClass().getMethod("queryStatsForPackage",java.util.UUID.class,String.class,handleType).invoke(storage,uuid,packageName,handle);
    legacyType.getField("codeSize").setLong(legacy,((Long)stats.getClass().getMethod("getAppBytes").invoke(stats)).longValue());
    legacyType.getField("dataSize").setLong(legacy,((Long)stats.getClass().getMethod("getDataBytes").invoke(stats)).longValue());
    legacyType.getField("cacheSize").setLong(legacy,((Long)stats.getClass().getMethod("getCacheBytes").invoke(stats)).longValue());
    succeeded=true;
   } catch(Exception deniedOrUnavailable) {android.util.Log.w("Kyf37StockCompat","Package storage query failed",deniedOrUnavailable);}
   try {
    Method callback=observer.getClass().getMethod("onGetStatsCompleted",Class.forName("android.content.pm.PackageStats"),boolean.class);
    callback.setAccessible(true);callback.invoke(observer,legacy,succeeded);
   } catch(Exception e){android.util.Log.w("Kyf37StockCompat","Package storage callback failed",e);}
  }},"Kyf37PackageStats").start();
 }
 public static android.net.Uri getContactLookupUri(android.content.ContentResolver resolver) {
  try {
   android.database.Cursor cursor=resolver.query(android.provider.ContactsContract.Profile.CONTENT_URI,null,null,null,null);
   boolean exists;
   try {exists=cursor!=null && cursor.moveToFirst();}
   finally {if(cursor!=null)cursor.close();}
   // Original OEM contract creates a local empty profile before resolving it.
   if(!exists)resolver.insert(android.provider.ContactsContract.Profile.CONTENT_RAW_CONTACTS_URI,new android.content.ContentValues());
   return android.provider.ContactsContract.Contacts.getLookupUri(resolver,android.provider.ContactsContract.Profile.CONTENT_URI);
  } catch(Exception deniedOrUnavailable) {return null;}
 }
 private static Context context() {
  try {
   Class<?> thread=Class.forName("android.app.ActivityThread");
   return (Context)thread.getMethod("currentApplication").invoke(null);
  } catch(Exception e) { throw new IllegalStateException("Application context unavailable",e); }
 }
 private static StorageVolume removable(boolean usb) {
  StorageManager manager=(StorageManager)context().getSystemService(Context.STORAGE_SERVICE);
  for(StorageVolume volume:manager.getStorageVolumes()) {
   if(!volume.isRemovable()||volume.isPrimary())continue;
   try {
    Object info=manager.getClass().getMethod("findVolumeById",String.class).invoke(manager,
      volume.getClass().getMethod("getId").invoke(volume));
    if(info==null)continue;
    Object disk=info.getClass().getMethod("getDisk").invoke(info);
    if(disk!=null && Boolean.TRUE.equals(disk.getClass().getMethod(usb?"isUsb":"isSd").invoke(disk)))return volume;
   } catch(Exception e) { throw new IllegalStateException("Cannot identify removable volume",e); }
  }
  return null;
 }
 private static File directory(boolean usb) {
  StorageVolume volume=removable(usb);
  if(volume==null)return null;
  try { return (File)volume.getClass().getMethod("getPathFile").invoke(volume); }
  catch(Exception e) { throw new IllegalStateException("Cannot resolve removable volume path",e); }
 }
 public static File getSecondaryStorageDirectory(){return directory(false);}
 public static File getUsbStorageDirectory(){return directory(true);}
 public static String getSecondaryStorageState(){StorageVolume v=removable(false);return v==null?Environment.MEDIA_REMOVED:v.getState();}
 public static String getUsbStorageState(){StorageVolume v=removable(true);return v==null?Environment.MEDIA_REMOVED:v.getState();}
 public static String formatNumberEx(String number){return PhoneNumberUtils.formatNumber(number,Locale.getDefault().getCountry());}
 public static android.net.Uri getBuzzerSoundsUri(Context original,int type){
  // Exact stock buzzer_sound_values/uri arrays: four shipped OEM sound files.
  if(original==null||type<0||type>3)return null;
  File file=new File("/system/media/audio/ui/0"+type+"_buzzer.mp3");
  if(!file.isFile())throw new IllegalStateException("Original emergency buzzer asset missing");
  return android.net.Uri.fromFile(file);
 }
 public static boolean endCall(Object legacyPhone) {
  Object telecom=context().getSystemService(Context.TELECOM_SERVICE);
  try{return Boolean.TRUE.equals(telecom.getClass().getMethod("endCall").invoke(telecom));}
  catch(Exception e){throw new IllegalStateException("End call denied or unavailable",e);}
 }
 private static int callState(){return ((android.telephony.TelephonyManager)context().getSystemService(Context.TELEPHONY_SERVICE)).getCallState();}
 public static boolean isIdle(Object legacyPhone){return callState()==android.telephony.TelephonyManager.CALL_STATE_IDLE;}
 public static boolean isOffhook(Object legacyPhone){return callState()==android.telephony.TelephonyManager.CALL_STATE_OFFHOOK;}
 public static boolean setWifiApEnabled(Object manager,android.net.wifi.WifiConfiguration config,boolean enabled){
  try {
   Object accepted=enabled?manager.getClass().getMethod("startSoftAp",android.net.wifi.WifiConfiguration.class).invoke(manager,config)
     :manager.getClass().getMethod("stopSoftAp").invoke(manager);
   return Boolean.TRUE.equals(accepted);
  } catch(Exception e){throw new IllegalStateException("Soft AP request denied or unavailable",e);}
 }
 private static Object credential(Object lock,String method){
  int user=android.os.Process.myUid()/100000;
  try{return lock.getClass().getMethod(method,int.class).invoke(lock,user);}
  catch(Exception e){throw new IllegalStateException("Credential query denied or unavailable",e);}
 }
 public static int getKeyguardStoredPasswordQuality(Object lock){return ((Integer)credential(lock,"getKeyguardStoredPasswordQuality")).intValue();}
 public static boolean isLockScreenDisabled(Object lock){return Boolean.TRUE.equals(credential(lock,"isLockScreenDisabled"));}
 public static boolean isSecure(Object lock){return Boolean.TRUE.equals(credential(lock,"isSecure"));}
 // Android 10 has no Lollipop Face Unlock package/password quality. This is
 // a removed capability, never a substitute for the real credential checks.
 public static boolean isBiometricWeakInstalled(Object lock){return false;}
 public static boolean usingBiometricWeak(Object lock){return false;}
 public static void setBacklightBrightness(android.os.PowerManager original,int value) {
  if(value<-1||value>255)throw new IllegalArgumentException("Brightness outside -1..255");
  Object display=context().getSystemService(Context.DISPLAY_SERVICE);
  try {display.getClass().getMethod("setTemporaryBrightness",int.class).invoke(display,value);}
  catch(Exception e){throw new IllegalStateException("Temporary brightness denied or unavailable",e);}
 }
 private Kyf37StockAppCompat(){}
}
