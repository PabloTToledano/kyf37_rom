package org.kyf37.compat;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.view.KeyEvent;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
/** Keypad playback and management for this dialer's private call memos. */
public final class CallMemoActivity extends Activity {
 private final ArrayList<File> files=new ArrayList<File>();private ListView list;private TextView empty;private MediaPlayer player;private File playing;
 @Override public void onCreate(Bundle state){
  setTheme(android.R.style.Theme_Material_NoActionBar);super.onCreate(state);
  LinearLayout page=new LinearLayout(this);page.setOrientation(1);page.setPadding(12,12,12,12);page.setBackgroundColor(0xff12263b);
  TextView title=new TextView(this);title.setText("Call memos");title.setTextSize(25);title.setTextColor(-1);page.addView(title);
  empty=new TextView(this);empty.setTextColor(-1);empty.setTextSize(16);page.addView(empty);
  list=new ListView(this);list.setOnItemClickListener(new android.widget.AdapterView.OnItemClickListener(){public void onItemClick(android.widget.AdapterView<?> a,android.view.View v,int position,long id){play(files.get(position));}});
  page.addView(list,new LinearLayout.LayoutParams(-1,0,1));setContentView(page);refresh();list.requestFocus();
 }
 private void refresh(){
  int selected=list.getSelectedItemPosition();files.clear();File folder=new File(getFilesDir(),"call-memos");File[] found=folder.listFiles();
  if(found!=null){Arrays.sort(found,new Comparator<File>(){public int compare(File a,File b){return Long.compare(b.lastModified(),a.lastModified());}});for(File file:found)if(file.isFile()&&file.getName().endsWith(".m4a"))files.add(file);}
  ArrayList<String> names=new ArrayList<String>();for(File file:files)names.add(new java.text.SimpleDateFormat("dd/MM HH:mm").format(new java.util.Date(file.lastModified()))+(file.getName().startsWith("automatic-pending-")?" · Pending":""));
  list.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_list_item_1,names));empty.setText(files.isEmpty()?"No recorded call memos.":"Select a memo and press OK to play.");
  if(!files.isEmpty())list.setSelection(Math.max(0,Math.min(selected,files.size()-1)));labels();
 }
 private void play(File file){
  android.telecom.TelecomManager telecom=(android.telecom.TelecomManager)getSystemService(TELECOM_SERVICE);
  if(telecom!=null&&telecom.isInCall()){Toast.makeText(this,"Finish the call before playing a memo",Toast.LENGTH_LONG).show();return;}
  if(file.equals(playing)){stop();return;}stop();MediaPlayer next=new MediaPlayer();
  try{next.setDataSource(file.getAbsolutePath());next.prepare();next.start();player=next;playing=file;
   next.setOnCompletionListener(new MediaPlayer.OnCompletionListener(){public void onCompletion(MediaPlayer p){stop();}});
   next.setOnErrorListener(new MediaPlayer.OnErrorListener(){public boolean onError(MediaPlayer p,int what,int extra){stop();Toast.makeText(CallMemoActivity.this,"Cannot play this memo",Toast.LENGTH_LONG).show();return true;}});labels();
  }catch(Exception e){next.release();Toast.makeText(this,"Cannot play this memo",Toast.LENGTH_LONG).show();}
 }
 private void stop(){if(player!=null){player.release();player=null;}playing=null;labels();}
 private void delete(){
  int position=list.getSelectedItemPosition();if(position<0||position>=files.size())return;final File file=files.get(position);
  new AlertDialog.Builder(this).setMessage("Delete this call memo?").setNegativeButton("Keep",null).setPositiveButton("Delete",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int button){if(file.equals(playing))stop();if(!file.delete())Toast.makeText(CallMemoActivity.this,"Cannot delete memo",Toast.LENGTH_LONG).show();refresh();}}).show();
 }
 private void labels(){
  try{Class<?> type=Class.forName("jp.kyocera.kcfp.util.KCfpSoftkeyGuide");Object guide=type.getMethod("getSoftkeyGuide",android.view.Window.class).invoke(null,getWindow());Method text=type.getMethod("setText",int.class,CharSequence.class);
   text.invoke(guide,0,player==null?"Play":"Stop");text.invoke(guide,1,"Back");text.invoke(guide,2,"Delete");text.invoke(guide,3,"Refresh");text.invoke(guide,4,"");type.getMethod("invalidate").invoke(guide);
  }catch(Exception e){android.util.Log.e("Kyf37Memo","Cannot display memo softkeys",e);}
 }
 @Override public boolean onKeyUp(int key,KeyEvent event){
  if(key==KeyEvent.KEYCODE_F1){finish();return true;}if(key==KeyEvent.KEYCODE_F2||key==KeyEvent.KEYCODE_DEL){delete();return true;}
  if(key==KeyEvent.KEYCODE_F3){refresh();return true;}if(key==KeyEvent.KEYCODE_0){stop();return true;}return super.onKeyUp(key,event);
 }
 @Override protected void onPause(){stop();super.onPause();}
}
