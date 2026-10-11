"""Exercise the actual Java theme loader with missing mappings/assets and cache changes."""
from pathlib import Path
import subprocess, tempfile

root = Path(__file__).resolve().parent.parent
stubs = {
'android/content/Context.java': '''package android.content; public class Context {
 public android.content.res.AssetManager getAssets(){return new android.content.res.AssetManager();}
 public android.content.res.Resources getResources(){return new android.content.res.Resources();}
 public Object getContentResolver(){return null;}}''',
'android/content/res/Resources.java': 'package android.content.res; public class Resources {}',
'android/content/res/AssetManager.java': '''package android.content.res; public class AssetManager {
 public java.io.InputStream open(String p) throws Exception {
 if(p.endsWith("packages.properties"))return new java.io.ByteArrayInputStream(
 "mapped=phone\\nplaceholder=generic\\nbroken=missing\\ncorrupt=corrupt\\n".getBytes());
 if(p.contains("missing"))throw new java.io.IOException();
 return new java.io.ByteArrayInputStream(p.getBytes());}}''',
'android/graphics/drawable/Drawable.java': '''package android.graphics.drawable; public class Drawable {
 public String path; public Drawable(String p){path=p;}
 public static Drawable createFromResourceStream(android.content.res.Resources r,Object v,java.io.InputStream in,String n)throws Exception {
 if(n.equals("corrupt"))return null;return new Drawable(new String(in.readAllBytes()));}
 public ConstantState getConstantState(){return new ConstantState(path);}
 public static class ConstantState {String p;ConstantState(String s){p=s;}
 public Drawable newDrawable(android.content.res.Resources r){return new Drawable(p);}}}''',
'android/util/Log.java': 'package android.util; public class Log {public static int e(String t,String m,Throwable e){return 0;}}',
'android/provider/Settings.java': '''package android.provider; public class Settings {
 public static class Global {public static int theme=1;public static int getInt(Object r,String k,int d){return theme;}}}''',
'Test.java': '''import org.kyf37.home.PastelIcons; public class Test {
 public static void main(String[] args){android.content.Context c=new android.content.Context();
 for(int theme=1;theme<=3;theme++) {android.provider.Settings.Global.theme=theme;
 for(String p:new String[]{"unknown","placeholder","broken","corrupt"})
 if(PastelIcons.get(c,p)!=null)throw new AssertionError(p);
 String folder=theme==1?"pastel-star/":theme==2?"sky-star/":"kyocera-classic/";
 for(int repeat=0;repeat<2;repeat++)if(!PastelIcons.get(c,"mapped").path.startsWith(folder))throw new AssertionError("theme cache");
 }System.out.println("PASS: unmapped, placeholder, missing and corrupt assets; mapped artwork and per-theme cache");}}'''
}
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    stubs['org/kyf37/home/PastelIcons.java'] = (root/'device-inspection/Kyf37PastelIcons.java.txt').read_text()
    for name, source in stubs.items():
        path = temp/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    jdk = Path('/home/pablo/kyf37-android10/prebuilts/jdk/jdk9/linux-x86/bin')
    if not jdk.exists():
        jdk = Path('/usr/bin')
    subprocess.run([str(jdk/'javac'), '-d', directory, *map(str,temp.rglob('*.java'))], check=True)
    subprocess.run([str(jdk/'java'), '-cp', directory, 'Test'], check=True)
