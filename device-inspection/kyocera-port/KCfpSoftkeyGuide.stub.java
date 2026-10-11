package jp.kyocera.kcfp.util;
import android.view.Window;
import android.graphics.Bitmap;
/** Compile-only declarations; the original stock class is shipped. */
public class KCfpSoftkeyGuide {
 public KCfpSoftkeyGuide(Window w){}
 public static KCfpSoftkeyGuide getSoftkeyGuide(Window w){return null;}
 public void setText(int i,CharSequence s){} public void setEnabled(int i,boolean b){}
 public void show(){} public void hide(){}
 public static class Softkeys {
  public Softkeys(){} public void mergeFrom(Softkeys s){}
  public CharSequence getText(int i){return null;} public boolean getEnabled(int i){return true;}public Bitmap getDrawable(int i){return null;}
 }
}
