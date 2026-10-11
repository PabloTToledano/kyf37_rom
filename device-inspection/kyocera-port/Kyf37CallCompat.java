package org.kyf37.compat;
import android.content.Context;
import android.graphics.drawable.Drawable;
import android.media.AudioManager;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.telecom.Call;
import android.telecom.InCallService;
import android.telecom.PhoneAccount;
import android.telecom.TelecomManager;
import android.telecom.VideoProfile;
import android.widget.Toast;
import java.io.File;
import java.lang.reflect.Method;
import java.util.WeakHashMap;
/** Concrete Android 10 migrations for the original dialer's supported operations. */
public final class Kyf37CallCompat {
 private static Context context;
 private static File pendingAutomaticMemo;
 private static boolean incallUiActive;private static int heardEffect=-1;
 private static final WeakHashMap<Call,Boolean> forwarding=new WeakHashMap<Call,Boolean>();
 private static final Handler ui=new Handler(Looper.getMainLooper());
 private static MediaRecorder recorder;private static Call recordingCall;private static File recordingFile;private static boolean recordingAutomatic;
 private static final WeakHashMap<Call,Call.Callback> observed=new WeakHashMap<Call,Call.Callback>();
 private static final WeakHashMap<Call,Boolean> automaticAttempted=new WeakHashMap<Call,Boolean>();
 private static final WeakHashMap<InCallService.VideoCall,InCallService.VideoCall.Callback> videoCallbacks=new WeakHashMap<InCallService.VideoCall,InCallService.VideoCall.Callback>();
 public static void attach(Context c){context=c.getApplicationContext();heardEffect=context.getSharedPreferences("kyf37-phone-compat",0).getInt("heard_effect",-1);}
 public static boolean hasMultipleCallCapableAccounts(TelecomManager manager){return manager.getCallCapablePhoneAccounts().size()>1;}
 public static Drawable createIconDrawable(PhoneAccount account,Context c){return account.getIcon()==null?null:account.getIcon().loadDrawable(c);}
 public static void deflectCall(Call call,String number){
  if(number==null||number.trim().length()==0)throw new IllegalArgumentException("Forwarding destination is empty");
  invoke(call,"deflect",new Class<?>[]{Uri.class},new Object[]{Uri.fromParts("tel",number,null)});
 }
 public static void destroy(Call call){
  stopTalkingMemo(call);InCallService.VideoCall video=call.getVideoCall();
  if(video!=null){InCallService.VideoCall.Callback callback=videoCallbacks.remove(video);if(callback!=null)video.unregisterCallback(callback);invoke(video,"destroy",new Class<?>[0],new Object[0]);}
 }
 public static int getCallSubstate(Call.Details details){Bundle b=details.getExtras();return b==null?0:b.getInt("callSubstate",0);}
 public static int getCodecMode(Call.Details details){Bundle b=details.getExtras();return b==null?0:b.getInt("codecMode",0);}
 public static int getSubState(Call call){observe(call);if(recordingCall==call&&recorder!=null)return 5;return getCallSubstate(call.getDetails());}
 public static int getRejectType(Call call){Bundle b=call.getDetails().getExtras();return b==null?0:b.getInt("rejectType",0);}
 public static void setReceiveMute(TelecomManager manager,boolean mute){
  if(context==null)throw new IllegalStateException("Phone app context is not initialized");
  AudioManager audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
  if(audio.getMode()!=AudioManager.MODE_IN_CALL)return;
  invoke(audio,"setParameters",new Class<?>[]{String.class},new Object[]{"rxvoice_mute_enabled="+mute});
 }
 public static synchronized void selectSaveAutoTalkMemo(TelecomManager manager,boolean save){
  File pending=pendingAutomaticMemo;if(pending==null)return;
  if(save){
   File saved=new File(pending.getParentFile(),"saved-"+pending.getName());
   if(!pending.renameTo(saved))throw new IllegalStateException("Cannot save automatic memo");
  }else if(pending.exists()&&!pending.delete())throw new IllegalStateException("Cannot discard automatic memo");
  pendingAutomaticMemo=null;
 }
 public static void setIncallUiActiveState(TelecomManager manager,boolean active){
  incallUiActive=active;
  // Original backend stores this flag; modern Telecom owns binding/visibility itself.
  if(!active&&recordingCall!=null&&recordingCall.getState()==Call.STATE_DISCONNECTED)stopTalkingMemo(recordingCall);
 }
 public static void setCallFowarding(Call call,boolean value){
  // Original method is a per-call forwarding/snooze marker, not a network forwarding request.
  forwarding.put(call,value);Bundle extras=new Bundle();extras.putBoolean("kyf37.call_forwarding",value);
  if(value)extras.putBoolean("kyf37.incoming_snooze",false);call.putExtras(extras);
 }
 public static void answerUnholding(Call call){
  if(call.getState()==Call.STATE_HOLDING)call.unhold();
  else if(call.getState()==Call.STATE_RINGING)call.answer(VideoProfile.STATE_AUDIO_ONLY);
  else throw new IllegalStateException("There is no held or ringing call to resume");
 }
 public static void setHeardEffect(Object phone,int mode){
  if(context==null)throw new IllegalStateException("Phone context not initialized");
  if(mode<0||mode>3)throw new IllegalArgumentException("Unknown receiver effect "+mode);
  heardEffect=mode;
  context.getSharedPreferences("kyf37-phone-compat",0).edit().putInt("heard_effect",mode).apply();
  AudioManager audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
  if(audio.getMode()==AudioManager.MODE_IN_CALL)invoke(audio,"setParameters",new Class<?>[]{String.class},new Object[]{mode==0?"voicefreq=off":"voicefreq=mode"+mode});
 }
 @SuppressWarnings("unchecked") public static void switchToOtherActiveSub(Object phone,String subscription,boolean retainHold){
  if(context==null)throw new IllegalStateException("Phone context not initialized");
  android.telephony.TelephonyManager telephony=(android.telephony.TelephonyManager)context.getSystemService(Context.TELEPHONY_SERVICE);
  if(telephony.getPhoneCount()<=1)return; // Same original DSDA guard; KYF37 is single-SIM.
  java.util.List<Call> calls=(java.util.List<Call>)invoke(phone,"getCalls",new Class<?>[0],new Object[0]);
  for(Call call:calls){
   android.telecom.PhoneAccountHandle handle=call.getDetails().getAccountHandle();
   if(handle==null)continue;
   if(handle.getId().equals(subscription)&&call.getState()==Call.STATE_HOLDING)call.unhold();
   else if(retainHold&&call.getState()==Call.STATE_ACTIVE&&call.getDetails().can(Call.Details.CAPABILITY_HOLD))call.hold();
  }
 }
 private static void observe(final Call call){
  if(observed.containsKey(call))return;
  Call.Callback callback=new Call.Callback(){
   @Override public void onStateChanged(Call c,int state){if(c==recordingCall&&state!=Call.STATE_ACTIVE)stopTalkingMemo(c);
    if(state==Call.STATE_ACTIVE&&heardEffect>=0)setHeardEffect(null,heardEffect);
    if(state==Call.STATE_ACTIVE)maybeAutomatic(c);}
   @Override public void onCallDestroyed(Call c){stopTalkingMemo(c);observed.remove(c);c.unregisterCallback(this);}
  };
  observed.put(call,callback);call.registerCallback(callback,ui);if(call.getState()==Call.STATE_ACTIVE)maybeAutomatic(call);
 }
 private static void maybeAutomatic(Call call){
  if(context!=null&&recorder==null&&!automaticAttempted.containsKey(call)&&android.provider.Settings.Global.getInt(context.getContentResolver(),"kyf37_auto_call_memo",0)==1){automaticAttempted.put(call,true);startMemo(call,true);}
 }
 public static synchronized void startTalkingMemo(final Call call){startMemo(call,false);}
 private static synchronized void startMemo(final Call call,boolean automatic){
  if(recorder!=null){if(recordingCall==call)return;throw new IllegalStateException("Another call is already recording");}
  if(context==null||call.getState()!=Call.STATE_ACTIVE)throw new IllegalStateException("A connected call is required");
  File folder=new File(context.getFilesDir(),"call-memos");if(!folder.exists()&&!folder.mkdirs())throw new IllegalStateException("Cannot create memo folder");
  final File file=new File(folder,(automatic?"automatic-pending-":"memo-")+System.currentTimeMillis()+".m4a");final MediaRecorder next=new MediaRecorder();
  try{
   next.setAudioSource(MediaRecorder.AudioSource.VOICE_CALL);next.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
   next.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);next.setOutputFile(file.getAbsolutePath());
   next.setMaxDuration(20*60*1000);next.setMaxFileSize(32*1024*1024);
   next.setOnInfoListener(new MediaRecorder.OnInfoListener(){public void onInfo(MediaRecorder r,int what,int extra){stopTalkingMemo(call);}});
   next.setOnErrorListener(new MediaRecorder.OnErrorListener(){public void onError(MediaRecorder r,int what,int extra){stopTalkingMemo(call);}});
   next.prepare();next.start();recorder=next;recordingCall=call;recordingFile=file;recordingAutomatic=automatic;observe(call);ui.post(new Runnable(){public void run(){Toast.makeText(context,"Recording call memo",Toast.LENGTH_SHORT).show();}});notifyUi(call);
  }catch(Exception e){next.release();file.delete();android.util.Log.e("Kyf37CallCompat","Call audio recording unavailable",e);ui.post(new Runnable(){public void run(){Toast.makeText(context,"Call memo recording is unavailable",Toast.LENGTH_LONG).show();}});notifyUi(call);}
 }
 public static synchronized void stopTalkingMemo(Call call){
  if(recorder==null||recordingCall!=call)return;
  MediaRecorder current=recorder;File file=recordingFile;boolean automatic=recordingAutomatic;recordingAutomatic=false;recorder=null;recordingCall=null;recordingFile=null;
  boolean saved=false;try{current.stop();saved=true;}catch(RuntimeException e){android.util.Log.e("Kyf37CallCompat","Memo was not finalized",e);}finally{current.release();}
  if(!saved&&file!=null)file.delete();
  if(saved&&automatic){if(pendingAutomaticMemo!=null&&pendingAutomaticMemo.exists())pendingAutomaticMemo.delete();pendingAutomaticMemo=file;}
  notifyUi(call);
 }
 private static void notifyUi(final Call call){ui.post(new Runnable(){public void run(){
  try{
   Class<?> listClass=Class.forName("com.android.incallui.CallList");Object list=listClass.getMethod("getInstance").invoke(null);
   Object wrapped=listClass.getMethod("getCallByTelecommCall",Call.class).invoke(list,call);
   if(wrapped!=null){
    try{Method update=wrapped.getClass().getDeclaredMethod("update");update.setAccessible(true);update.invoke(wrapped);}catch(NoSuchMethodException ignored){}
    listClass.getMethod("onUpdate",Class.forName("com.android.incallui.Call")).invoke(list,wrapped);
   }
  }catch(Exception e){android.util.Log.w("Kyf37CallCompat","Cannot refresh original memo UI",e);}
 }});}
 private static Object invoke(Object target,String name,Class<?>[] types,Object[] args){
  try{Method method=target.getClass().getMethod(name,types);method.setAccessible(true);return method.invoke(target,args);}
  catch(Exception e){throw new IllegalStateException("Android call operation failed: "+name,e);}
 }
 private static void callback(Object listener,String name,Object...args){
  try{
   for(Method method:listener.getClass().getMethods()){
    if(!method.getName().equals(name)||method.getParameterTypes().length!=args.length)continue;
    method.setAccessible(true);method.invoke(listener,args);return;
   }
   android.util.Log.w("Kyf37CallCompat","Legacy video callback missing: "+name);
  }catch(Exception e){android.util.Log.e("Kyf37CallCompat","Legacy video callback failed: "+name,e);}
 }
 public static void setVideoCallListener(final InCallService.VideoCall call,final Object listener){
  InCallService.VideoCall.Callback old=videoCallbacks.remove(call);if(old!=null)call.unregisterCallback(old);if(listener==null)return;
  InCallService.VideoCall.Callback next=new InCallService.VideoCall.Callback(){
   public void onSessionModifyRequestReceived(VideoProfile profile){callback(listener,"onSessionModifyRequestReceived",profile);}
   public void onSessionModifyResponseReceived(int status,VideoProfile requested,VideoProfile response){callback(listener,"onSessionModifyResponseReceived",status,requested,response);}
   public void onCallSessionEvent(int event){callback(listener,"onCallSessionEvent",event);}
   public void onPeerDimensionsChanged(int width,int height){callback(listener,"onPeerDimensionsChanged",width,height);}
   public void onCallDataUsageChanged(long usage){callback(listener,"onCallDataUsageChanged",usage);}
   public void onCameraCapabilitiesChanged(VideoProfile.CameraCapabilities caps){
    try{Object legacy=Class.forName("android.telecom.CameraCapabilities").getConstructor(boolean.class,float.class,int.class,int.class).newInstance(invoke(caps,"isZoomSupported",new Class<?>[0],new Object[0]),invoke(caps,"getMaxZoom",new Class<?>[0],new Object[0]),caps.getWidth(),caps.getHeight());callback(listener,"onCameraCapabilitiesChanged",legacy);}
    catch(Exception e){android.util.Log.e("Kyf37CallCompat","Camera capability translation failed",e);}
   }
   public void onVideoQualityChanged(int quality){callback(listener,"onVideoQualityChanged",quality);}
  };
  videoCallbacks.put(call,next);call.registerCallback(next);
 }
}
