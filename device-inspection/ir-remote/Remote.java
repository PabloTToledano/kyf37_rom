package org.kyf37.remote;
import android.app.*;
import android.content.*;
import android.hardware.ConsumerIrManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Offline keypad remote. No network, learning claims, automatic scanning or boot service. */
public final class Remote extends Activity {
 LinearLayout root, controls; TextView status,subtitle; ScrollView scroll;
 final ArrayList<Button> buttons=new ArrayList<>(); final AtomicBoolean busy=new AtomicBoolean();
 final ExecutorService worker=Executors.newSingleThreadExecutor();
 volatile boolean visible; int profile=-1,flags=0,temp=24,mode=1,fan=0; boolean power=true,swing=false;
 volatile android.net.LocalSocket transmitterSocket;
 boolean frameworkFocus;
 JSONArray custom; String customName="Imported remote"; ConsumerIrManager ir;
 static final String[] NAMES={"Samsung TV (Samsung32)","LG TV (NEC)","Sony TV (SIRC-12)","Gree AC (YAW1F)","Gree AC (YBOFB)"};
 static final String[] TV={"Power","Volume +","Volume −","Channel +","Channel −","Mute","Input"};
 static final int[][] CODES={{2,7,11,18,16,15,1},{8,2,3,0,1,9,11},{21,18,19,16,17,20,37}};
 @Override public void onCreate(Bundle saved){super.onCreate(saved);ir=(ConsumerIrManager)getSystemService(CONSUMER_IR_SERVICE);
  try{Class.forName("android.view.Kyf37FocusTheme");frameworkFocus=true;}catch(Exception ignored){}
  android.content.SharedPreferences p=getPreferences(0);flags=p.getInt("flags",0);temp=p.getInt("temp",24);mode=p.getInt("mode",1);fan=p.getInt("fan",0);power=p.getBoolean("power",true);swing=p.getBoolean("swing",false);
  try{JSONObject c=new JSONObject(p.getString("custom","{}"));if(c.has("commands")){validateProfile(c);custom=c.getJSONArray("commands");customName=c.getString("name");}}catch(Exception ignored){}
  profile=saved==null?p.getInt("profile",-1):saved.getInt("profile",-1);if(profile>5||profile< -1||(profile==5&&custom==null))profile=-1;render();
 }
 @Override protected void onResume(){super.onResume();visible=true;}
 @Override protected void onPause(){visible=false;android.net.LocalSocket s=transmitterSocket;if(s!=null)try{s.close();}catch(IOException ignored){}save();super.onPause();}
 @Override protected void onDestroy(){worker.shutdown();super.onDestroy();}
 @Override protected void onSaveInstanceState(Bundle b){b.putInt("profile",profile);super.onSaveInstanceState(b);}
 void save(){getPreferences(0).edit().putInt("profile",profile).putInt("flags",flags).putInt("temp",temp).putInt("mode",mode).putInt("fan",fan).putBoolean("power",power).putBoolean("swing",swing).apply();}
 int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+0.5f);}
 TextView text(String s,int size){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(dp(10),dp(6),dp(10),dp(6));return t;}
 void render(){
  buttons.clear();root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xff14243b);setContentView(root);
  TextView title=text("IR Remote",27);title.setTypeface(null,Typeface.BOLD);root.addView(title);
  subtitle=text("",16);root.addView(subtitle);updateSubtitle();
  root.addView(text(profile<0?"D-pad selects · OK opens":"D-pad selects · OK sends · 0 profiles",14));
  status=text("Aim the infrared port at your device.\nDevice response is not confirmed by the app.",15);root.addView(status);
  scroll=new ScrollView(this);controls=new LinearLayout(this);controls.setOrientation(1);scroll.addView(controls);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  if(profile<0){
   for(int i=0;i<NAMES.length;i++){final int n=i;add((i+1)+"  "+NAMES[i],()->{profile=n;render();save();});}
   if(custom!=null)add("6  "+customName,()->{profile=5;render();save();});
   add("Import remote / AC commands",()->importProfile());add("Check transmitter",()->probe());add("Transmitter settings",()->options());
  }else if(profile<3){for(int i=0;i<TV.length;i++){final int n=i;add((i+1)+"  "+TV[i],()->sendTv(n));}}
  else if(profile==3||profile==4){
   add("1  Power ON",()->{power=true;updateSubtitle();sendAc();});add("2  Power OFF",()->{power=false;updateSubtitle();sendAc();});
   add("3  Temperature +",()->{temp=Math.min(30,temp+1);updateSubtitle();save();});add("4  Temperature −",()->{temp=Math.max(16,temp-1);updateSubtitle();save();});
   add("5  Mode",()->{mode=(mode+1)%5;updateSubtitle();save();});add("6  Fan",()->{fan=(fan+1)%4;updateSubtitle();save();});
   add("7  Swing",()->{swing=!swing;updateSubtitle();save();});add("8  Send settings",()->sendAc());
  }else{for(int i=0;i<custom.length();i++){final int n=i;add((i<9?(i+1)+"  ":"")+custom.optJSONObject(i).optString("name"),()->sendCustom(n));}}
  if(!buttons.isEmpty())buttons.get(0).requestFocus();
 }
 void updateSubtitle(){
  String name=profile<0?"Choose a remote":profile==5?customName:NAMES[profile];
  if(profile==3||profile==4)name+="\nRequested: "+(power?"ON":"OFF")+" · "+(mode==0?25:temp)+"°C · "+new String[]{"Auto","Cool","Dry","Fan","Heat"}[mode]+"\nFan "+(mode==2?1:fan)+" · Swing "+(swing?"ON":"OFF")+" · 8 sends changes";
  subtitle.setText(name);
 }
 void add(String label,Runnable action){Button b=new Button(this);b.setText(label);b.setTextSize(18);b.setTextColor(Color.WHITE);b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);b.setAllCaps(false);b.setPadding(dp(16),0,dp(8),0);b.setMinHeight(dp(54));
  GradientDrawable base=new GradientDrawable();base.setColor(0xff1b314d);base.setCornerRadius(dp(7));base.setStroke(dp(1),0xff57708c);b.setBackground(base);
  b.setOnFocusChangeListener((v,focused)->{boolean fallback=focused&&!frameworkFocus;GradientDrawable d=new GradientDrawable();d.setColor(fallback?0xff24466c:0xff1b314d);d.setCornerRadius(dp(7));d.setStroke(dp(fallback?4:1),fallback?0xff78cfff:0xff57708c);v.setBackground(d);});
  b.setOnClickListener(v->{if(!busy.get())action.run();});buttons.add(b);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(56));lp.setMargins(dp(8),dp(3),dp(8),dp(3));controls.addView(b,lp);
 }
 @Override public boolean dispatchKeyEvent(KeyEvent e){
  int k=e.getKeyCode();boolean digit=k>=KeyEvent.KEYCODE_0&&k<=KeyEvent.KEYCODE_9;
  if(digit||k==KeyEvent.KEYCODE_STAR||k==KeyEvent.KEYCODE_POUND||k==KeyEvent.KEYCODE_DPAD_CENTER||k==KeyEvent.KEYCODE_ENTER){
   if(e.getAction()!=KeyEvent.ACTION_DOWN||e.getRepeatCount()!=0)return true;
   if(busy.get())return true;
   if(k==KeyEvent.KEYCODE_STAR){probe();return true;}if(k==KeyEvent.KEYCODE_POUND){options();return true;}
   if(k==KeyEvent.KEYCODE_0){profile=-1;render();save();return true;}
   if(digit){int n=k-KeyEvent.KEYCODE_1;if(n>=0&&n<buttons.size()){buttons.get(n).requestFocus();buttons.get(n).performClick();}return true;}
   View v=getCurrentFocus();if(v instanceof Button)v.performClick();return true;
  }return super.dispatchKeyEvent(e);
 }
 @Override public void onBackPressed(){if(profile>=0){profile=-1;render();save();}else super.onBackPressed();}
 void sendTv(int n){IrSignals.Wave w=profile==2?IrSignals.sony(1,CODES[2][n]):IrSignals.nec(profile==0?0x0707:4,CODES[profile][n],profile==0);transmit(w);}
 void sendAc(){transmit(IrSignals.gree(IrSignals.greeState(power,temp,mode,fan,swing,profile==3)));save();}
 void sendCustom(int n){try{transmit(decode(custom.getJSONObject(n)));}catch(Exception e){status.setText("Invalid command: "+e.getMessage());}}
 static IrSignals.Wave decode(JSONObject c)throws Exception{
  String protocol=c.optString("protocol","raw").toLowerCase(Locale.ROOT);
  if(protocol.equals("nec")||protocol.equals("samsung"))return IrSignals.nec(c.getInt("address"),c.getInt("command"),protocol.equals("samsung"));
  if(protocol.equals("sony12"))return IrSignals.sony(c.getInt("address"),c.getInt("command"));
  if(!protocol.equals("raw"))throw new IllegalArgumentException("Unknown protocol "+protocol);
  JSONArray a=c.getJSONArray("timings");if(a.length()>1024)throw new IllegalArgumentException("Too many timings");int[] p=new int[a.length()];for(int i=0;i<p.length;i++)p[i]=a.getInt(i);
  return new IrSignals.Wave(c.getInt("frequency"),p);
 }
 static void validateProfile(JSONObject p)throws Exception{
  String name=p.getString("name");if(name.length()<1||name.length()>64)throw new IllegalArgumentException("Remote name must be 1–64 characters");
  JSONArray a=p.getJSONArray("commands");if(a.length()<1||a.length()>80)throw new IllegalArgumentException("1–80 commands required");
  for(int i=0;i<a.length();i++){JSONObject c=a.getJSONObject(i);String n=c.getString("name");if(n.length()<1||n.length()>64)throw new IllegalArgumentException("Invalid command name");decode(c);}
 }
 void importProfile(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);try{startActivityForResult(i,10);}catch(Exception e){status.setText("No document picker available");}}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=10||result!=RESULT_OK||data==null)return;
  try(InputStream in=getContentResolver().openInputStream(data.getData());ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>512000)throw new IOException("File exceeds 500 KB");out.write(b,0,n);}
   JSONObject p=new JSONObject(out.toString("UTF-8"));validateProfile(p);custom=p.getJSONArray("commands");customName=p.getString("name");getPreferences(0).edit().putString("custom",p.toString()).apply();profile=5;render();
  }catch(Exception e){status.setText("Import failed: "+e.getMessage());}
 }
 void options(){String[] choices={"Normal pulses","Narrow pulses (2 µs)","Inverted normal pulses","Inverted narrow pulses"};new AlertDialog.Builder(this).setTitle("GPIO transmitter pulse mode").setSingleChoiceItems(choices,new int[]{0,2,1,3}[flags],(d,n)->{flags=new int[]{0,2,1,3}[n];save();d.dismiss();status.setText("Pulse mode saved. # settings · * check");}).setNegativeButton("Back",null).show();}
 boolean standard(){return ir!=null&&ir.hasIrEmitter();}
 void probe(){run(null);}
 void transmit(IrSignals.Wave w){run(w);}
 void run(final IrSignals.Wave w){if(!busy.compareAndSet(false,true))return;status.setText(w==null?"Checking transmitter…":"Sending…");
  worker.execute(()->{String message;try{
   if(!visible)throw new IOException("App left foreground; cancelled");
   if(standard()){
    if(w!=null){ConsumerIrManager.CarrierFrequencyRange[] ranges=ir.getCarrierFrequencies();boolean valid=false;if(ranges!=null)for(ConsumerIrManager.CarrierFrequencyRange r:ranges)if(w.hz>=r.getMinFrequency()&&w.hz<=r.getMaxFrequency())valid=true;if(!valid)throw new IOException("Carrier frequency unsupported");ir.transmit(w.hz,w.timings);}
    message=w==null?"Android IR transmitter available":"Signal sent; device response unconfirmed";
   }else message=rootTransmit(w);
  }catch(Exception e){message="Unable to transmit: "+e.getMessage();}finally{busy.set(false);}
  final String result=message;runOnUiThread(()->{if(!isFinishing())status.setText(result);});
 });}
 String rootTransmit(IrSignals.Wave w)throws Exception{
  android.net.LocalSocket socket=new android.net.LocalSocket();transmitterSocket=socket;
  try{
   socket.connect(new android.net.LocalSocketAddress("kyf37_ir_remote",android.net.LocalSocketAddress.Namespace.RESERVED));socket.setSoTimeout(12000);
   if(!visible)throw new IOException("App left foreground; cancelled");
   OutputStream out=socket.getOutputStream();out.write(w==null?'P':'S');
   if(w!=null){StringBuilder s=new StringBuilder().append(w.hz).append(' ').append(w.timings.length).append(' ').append(flags);for(int t:w.timings)s.append(' ').append(t);s.append('\n');out.write(s.toString().getBytes("US-ASCII"));}
   out.flush();socket.shutdownOutput();
   ByteArrayOutputStream result=new ByteArrayOutputStream();InputStream in=socket.getInputStream();byte[] b=new byte[512];int n;
   while((n=in.read(b))>0){if(result.size()+n>4096)throw new IOException("Invalid transmitter reply");result.write(b,0,n);}
   String reply=result.toString("UTF-8").trim();if(reply.isEmpty())throw new IOException("Transmitter service unavailable");return reply;
  }finally{socket.close();transmitterSocket=null;}
 }
}
