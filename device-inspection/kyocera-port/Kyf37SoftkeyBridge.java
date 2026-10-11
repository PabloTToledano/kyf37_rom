package jp.kyocera.kcfp.util;
import android.app.Dialog;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.text.TextUtils;
import android.view.View;
import android.view.Window;
import android.widget.FrameLayout;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;
/** Window-local replacement for the original Kyocera Window softkey ABI. */
public final class Kyf37SoftkeyBridge {
 private static boolean supported(android.content.Context context){
  String name=context.getPackageName();
  try {
   java.io.InputStream input=context.getAssets().open("kyf37-native-softkeys/package.txt");
   try {
    byte[] bytes=new byte[256];int length=input.read(bytes);
    if(length>0 && name.equals(new String(bytes,0,length,"UTF-8").trim()))return true;
   } finally {input.close();}
  } catch(java.io.IOException absent) { /* Older supported ports use the list below. */ }
  return "jp.kyocera.afphome".equals(name)||"org.kyf37.dialerxx".equals(name)
   ||"jp.kyocera.camera".equals(name)||"jp.kyocera.memo".equals(name)
   ||"jp.kyocera.barcodereader".equals(name)||"jp.kyocera.kc_soundrecorder".equals(name)
   ||"jp.kyocera.kc_soundrecorder.manager".equals(name)||"jp.kyocera.mobilelight".equals(name);
 }
 public static String resourcesPackage(android.content.Context context){
  try{return context.getResources().getResourcePackageName(context.getApplicationInfo().icon);}
  catch(android.content.res.Resources.NotFoundException e){return context.getPackageName();}
 }
 private static final WeakHashMap<Window,WeakReference<Session>> sessions=new WeakHashMap<Window,WeakReference<Session>>();
 private static synchronized Session session(Window window){
  WeakReference<Session> ref=sessions.get(window);Session s=ref==null?null:ref.get();
  if(s==null){s=new Session(window);sessions.put(window,new WeakReference<Session>(s));}return s;
 }
 public static KCfpSoftkeyGuide getSoftkeyGuide(Window w){return w==null?null:session(w).guide;}
 public static KCfpSoftkeyGuide.Softkeys getCurrentSoftkeys(Window w){return session(w).keys;}
 public static KCfpSoftkeyGuide.Softkeys getAttributSoftkeys(Window w){return session(w).keys;}
 public static void setSoftkeys(Window w,KCfpSoftkeyGuide.Softkeys keys){Session s=session(w);s.keys.mergeFrom(keys);s.refresh();}
 public static void show(Window w,boolean visible){Session s=session(w);s.visible=visible;s.refresh();}
 public static void assignDialog(Dialog d,boolean assign){Kyf37DialogSoftkeys.getInstance().assignButtonToSoftkey(d,assign);}
 private static final class Session {
  final Window window;final KCfpSoftkeyGuide guide;final KCfpSoftkeyGuide.Softkeys keys=new KCfpSoftkeyGuide.Softkeys();
  boolean visible=true;Bar bar;View content;int left,top,right,bottom;
  Session(Window w){window=w;guide=new KCfpSoftkeyGuide(w);}
  void refresh(){window.getDecorView().post(new Runnable(){public void run(){attach();}});}
  void attach(){
   if(!supported(window.getContext()))return;
   View root=window.getDecorView().findViewById(android.R.id.content);
   if(!(root instanceof FrameLayout))return;
   FrameLayout frame=(FrameLayout)root;
   if(bar==null||bar.getParent()!=frame){
    if(content!=null)content.setPadding(left,top,right,bottom);
    content=frame.getChildCount()==0?null:frame.getChildAt(0);
    if(content!=null){left=content.getPaddingLeft();top=content.getPaddingTop();right=content.getPaddingRight();bottom=content.getPaddingBottom();}
    bar=new Bar(this);frame.addView(bar,new FrameLayout.LayoutParams(-1,bar.height,android.view.Gravity.BOTTOM));
   }
   bar.setVisibility(visible?View.VISIBLE:View.GONE);
   if(content!=null)content.setPadding(left,top,right,bottom+(visible?bar.height:0));
   bar.invalidate();
  }
 }
 private static final class Bar extends View {
  final Session s;final int height;final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
  final Bitmap[] artwork=new Bitmap[6];
  Bar(Session session){super(session.window.getContext());s=session;height=Math.round(60*getResources().getDisplayMetrics().density);setFocusable(false);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);

  }
  void image(Canvas canvas,int index,float left,float top,float right,float bottom){if(artwork[index]!=null)canvas.drawBitmap(artwork[index],null,new RectF(left,top,right,bottom),paint);}
  @Override protected void onDraw(Canvas canvas){
   canvas.drawColor(0xff101722);float left=getWidth()*.36f,right=getWidth()*.64f,half=getHeight()/2f;
   // Physical positions: F1/F2 above the D-pad, F3/F4 below it.
   cell(canvas,1,0,0,left,half,"");cell(canvas,3,0,half,left,getHeight(),"");
   cell(canvas,0,left,0,right,getHeight(),"OK");cell(canvas,2,right,0,getWidth(),half,"");cell(canvas,4,right,half,getWidth(),getHeight(),"");
  }

  void cell(Canvas c,int index,float left,float top,float right,float bottom,String key){
   CharSequence raw=s.keys.getText(index);String label=raw==null?"":raw.toString();
   if(label.startsWith("@SK_AUTO")){
    View focus=s.window.getCurrentFocus();
    label=label.contains("MENU")?"Menu":focus instanceof android.widget.TextView?((android.widget.TextView)focus).getText().toString():"Select";
   }
   Bitmap icon=s.keys.getDrawable(index);float d=getResources().getDisplayMetrics().density;
   float x=(left+right)/2f,y=(top+bottom)/2f;
   paint.setColor(s.keys.getEnabled(index)?0xffffffff:0xff8294a5);paint.setTextSize(12*getResources().getDisplayMetrics().scaledDensity);paint.setTextAlign(Paint.Align.CENTER);
   paint.setColor(index==0?0xff29446a:0xff1c2839);
   c.drawRoundRect(new RectF(left+3*d,top+3*d,right-3*d,bottom-3*d),8*d,8*d,paint);
   paint.setColor(s.keys.getEnabled(index)?0xffedf3ff:0xff8294a5);
   if(index>0)keyIcon(c,index,left+12*d,y,d);
   x+=index>0?7*d:0;
   String text=label.length()==0?key:label;
   text=TextUtils.ellipsize(text,new android.text.TextPaint(paint),right-left-(index>0?30:8)*d,TextUtils.TruncateAt.END).toString();
   if(icon!=null&&!icon.isRecycled()){
    float size=Math.min(16*d,bottom-top-4*d);c.drawBitmap(icon,null,new RectF(right-size-3*d,y-size/2,right-3*d,y+size/2),paint);
    x-=size/2;text=TextUtils.ellipsize(text,new android.text.TextPaint(paint),right-left-size-(index>0?30:10)*d,TextUtils.TruncateAt.END).toString();
   }
   c.drawText(text,x,y-(paint.ascent()+paint.descent())/2,paint);
  }
  private void keyIcon(Canvas c, int key, float x, float y, float d) {
        paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(1.2f*d);
        if (key==1) { // Phone book
            c.drawRoundRect(x-5*d,y-6*d,x+5*d,y+6*d,1*d,1*d,paint);
            c.drawCircle(x,y-2*d,1.5f*d,paint); c.drawLine(x-3*d,y+3*d,x+3*d,y+3*d,paint);
        } else if (key==2) { // Camera
            c.drawRoundRect(x-6*d,y-4*d,x+6*d,y+5*d,1*d,1*d,paint);
            c.drawCircle(x,y,2.5f*d,paint); c.drawLine(x-3*d,y-6*d,x+2*d,y-6*d,paint);
        } else if (key==3) { // Mail
            c.drawRect(x-6*d,y-4*d,x+6*d,y+4*d,paint);
            c.drawLine(x-6*d,y-4*d,x,y+1*d,paint); c.drawLine(x,y+1*d,x+6*d,y-4*d,paint);
        } else { // Browser
            c.drawCircle(x,y,6*d,paint); c.drawOval(x-2.5f*d,y-6*d,x+2.5f*d,y+6*d,paint);
            c.drawLine(x-6*d,y,x+6*d,y,paint);
        }
        paint.setStyle(Paint.Style.FILL);
  }

 }
}
