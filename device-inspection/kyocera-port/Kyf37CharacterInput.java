package org.kyf37.stockcompat;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.view.inputmethod.InputMethodManager;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.content.Context;

/** Replace only the obsolete OEM IME private-command editor, keeping the stock viewer. */
public final class Kyf37CharacterInput {
 public static void show(final Activity activity, String previous) {
  final String old=previous==null?"":previous;
  final EditText edit=new EditText(activity);
  edit.setSingleLine(true); edit.setTextSize(28); edit.setHint("Enter characters");
  edit.setText(old); edit.setSelectAllOnFocus(true);
  edit.setImeOptions(EditorInfo.IME_ACTION_DONE);
  final AlertDialog dialog=new AlertDialog.Builder(activity).setTitle("Kanji Check")
   .setView(edit).setPositiveButton("Check",new DialogInterface.OnClickListener(){
    public void onClick(DialogInterface d,int which){finish(activity,edit,"g");}
   }).setNegativeButton(android.R.string.cancel,new DialogInterface.OnClickListener(){
    public void onClick(DialogInterface d,int which){cancel(activity,old);}
   }).setOnCancelListener(new DialogInterface.OnCancelListener(){
    public void onCancel(DialogInterface d){cancel(activity,old);}
   }).create();
  edit.setOnEditorActionListener(new android.widget.TextView.OnEditorActionListener(){
   public boolean onEditorAction(android.widget.TextView v,int action,android.view.KeyEvent event){
    if(action==EditorInfo.IME_ACTION_DONE){dialog.dismiss();finish(activity,edit,"g");return true;}
    return false;
   }
  });
  dialog.show(); edit.requestFocus();
 }
 private static void finish(Activity a,EditText edit,String method){
  ((InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE))
   .hideSoftInputFromWindow(edit.getWindowToken(),0);
  call(a,method,edit.getText().toString());
 }
 private static void cancel(Activity a,String old){call(a,"h",old);}
 private static void call(Activity a,String method,String value){
  try{a.getClass().getMethod(method,String.class).invoke(a,value);}
  catch(Exception e){throw new IllegalStateException("Stock character callback failed",e);}
 }
}
