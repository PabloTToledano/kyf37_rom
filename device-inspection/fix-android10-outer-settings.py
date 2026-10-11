#!/usr/bin/env python3
"""Outer (128x36) screen: screen-off timeout + persistent options (Settings.Global kyf37_outer_*).

Idempotent; WSL Python 3. Run AFTER fix-android10-outer-animation.py (which regenerates the service,
renderer and controller from templates every build, so fix-android10-outer-animation.py chains this
script at its end). Phone-settings / Settings entries are persistent edits of the tree and also
idempotent.

Keys (Settings.Global, ints; defaults are in code, userdata is never touched by the installer):
  kyf37_outer_clock_size   0 small, 1 medium, 2 large          (default 2)
  kyf37_outer_time_format  0 24-hour, 1 12-hour                (default 0)
  kyf37_outer_seconds      0/1                                 (default 0)
  kyf37_outer_battery      0 off, 1 icon, 2 percent, 3 both    (default 3)
  kyf37_outer_timeout      seconds the panel stays lit, 0=always (default 10)
  kyf37_outer_animation    0/1 character scenes + idle mascot  (default 1)
  kyf37_outer_badapple     0/1 long-press Bad Apple            (default 1)
"""
from pathlib import Path
import re, shutil

W = Path(__file__).resolve().parent
ROOT = Path.home() / 'kyf37-android10'
APP = ROOT / 'packages/apps/Kyf37OuterScreen'
PHONE = ROOT / 'packages/apps/Kyf37PhoneSettings'
SETTINGS = ROOT / 'packages/apps/Settings'
MARK = 'KYF37_OUTER_SETTINGS'


def sub(s, old, new, count=1):
    assert old in s, 'anchor missing: ' + old[:70]
    return s.replace(old, new, count)


# ------------------------------------------------------------------ Java service
def patch_service():
    p = APP / 'src/org/kyf37/subdisplay/OuterScreenService.java'
    s = p.read_text()
    if MARK in s:
        return
    s = sub(s, 'import java.util.Calendar;', 'import java.util.Calendar;\nimport android.database.ContentObserver;')
    s = sub(s, '    private static native int updateAnimation(int frame,int hour,int minute,int battery,int scene);',
            '    private static native int updateAnimation(int frame,int hour,int minute,int battery,int scene);\n'
            '    private static native void configure(int size,int fmt12,int seconds,int battery,int mascot,int second);')
    s = sub(s, '    private AlarmManager alarms;', '''    // %s
    private long litUntil;
    private boolean wasClosed;
    private boolean blanked;
    private ContentObserver outerObserver;
    private static final String[] OUTER_KEYS={"kyf37_outer_clock_size","kyf37_outer_time_format","kyf37_outer_seconds",
        "kyf37_outer_battery","kyf37_outer_timeout","kyf37_outer_animation","kyf37_outer_badapple"};
    private int cfg(String key,int def){return android.provider.Settings.Global.getInt(getContentResolver(),key,def);}
    private int timeoutMs(){int t=cfg("kyf37_outer_timeout",10);return t<=0?0:Math.min(t,3600)*1000;}
    private boolean animationOn(){return cfg("kyf37_outer_animation",1)!=0;}
    private boolean badAppleOn(){return cfg("kyf37_outer_badapple",1)!=0;}
    private boolean secondsOn(){return cfg("kyf37_outer_seconds",0)!=0;}
    /** True while the panel should be lit: playing something, or inside the screen-off timeout. */
    private boolean lit(){return movie||animating||SystemClock.elapsedRealtime()<litUntil;}
    private void light(){int t=timeoutMs();litUntil=t==0?Long.MAX_VALUE:SystemClock.elapsedRealtime()+t;}
    private void applyConfig(){
        blanked=false;
        configure(cfg("kyf37_outer_clock_size",2),cfg("kyf37_outer_time_format",0),secondsOn()?1:0,
            cfg("kyf37_outer_battery",3),animationOn()?1:0,Calendar.getInstance().get(Calendar.SECOND));
    }

    private AlarmManager alarms;''' % MARK)
    s = sub(s, 'movie=true;movieStart=SystemClock.elapsedRealtime();', 'movie=true;blanked=false;movieStart=SystemClock.elapsedRealtime();')
    s = sub(s, 'if(sideHeld && closed()) {', 'if(sideHeld && closed() && badAppleOn()) {')
    s = sub(s, '            sideHeld=true;stopAnimation();startAnimation();',
            '            boolean wasLit=lit();light();sideHeld=true;\n'
            '            if(wasLit && animationOn()){stopAnimation();startAnimation();} else {stopAnimation();refresh();}')
    s = sub(s, 'SystemClock.elapsedRealtime()>=animationDeadline) {\n                stopAnimation();refresh();return;',
            'SystemClock.elapsedRealtime()>=animationDeadline) {\n                if(closed())light();stopAnimation();refresh();return;')
    s = sub(s, '            int result=updateAnimation(frame++,', '            applyConfig();\n            int result=updateAnimation(frame++,')
    s = sub(s, 'if(was)Log.i("KYF37OuterScreen","BadApple stopped");',
            'if(was)Log.i("KYF37OuterScreen","BadApple stopped");\n        if(was && closed())light();')
    s = sub(s, '        boolean visible=closed();',
            '        boolean lidClosed=closed();\n        if(lidClosed && !wasClosed)light();\n        wasClosed=lidClosed;\n'
            '        boolean visible=lidClosed && lit();')
    s = sub(s, 'if(!visible) {sideHeld=false;', 'if(!lidClosed) {sideHeld=false;')
    s = sub(s, '''            int result=visible?updateAnimation(-1,now.get(Calendar.HOUR_OF_DAY),now.get(Calendar.MINUTE),battery,
                (idlePhase++ & 3)):updatePanel(false,0,0,0);''',
            '''            int result;
            if(visible) {
                applyConfig();blanked=false;
                result=updateAnimation(-1,now.get(Calendar.HOUR_OF_DAY),now.get(Calendar.MINUTE),battery,
                    (int)((SystemClock.elapsedRealtime()/5000)&3));
            } else if(!blanked) {
                result=updatePanel(false,0,0,0);
                if(result==0)blanked=true;
            } else result=0;''')
    s = sub(s, '''            if(visible)alarms.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP,
                SystemClock.elapsedRealtime()+5000,tick);''',
            '''            if(visible) {
                long step=secondsOn()?1000:5000;
                long left=litUntil-SystemClock.elapsedRealtime();
                if(left>0 && left<step)step=Math.max(50,left);
                alarms.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP,SystemClock.elapsedRealtime()+step,tick);
            }''')
    s = sub(s, 'if(!inputReady) {if(movie){stopMovie();refresh();}else{stopAnimation();startAnimation();}}',
            'if(!inputReady) {if(movie){stopMovie();refresh();}else{boolean wasLit=lit();light();stopAnimation();'
            'if(wasLit && animationOn())startAnimation();else refresh();}}')
    s = sub(s, '        alarms=(AlarmManager)getSystemService(ALARM_SERVICE);',
            '''        alarms=(AlarmManager)getSystemService(ALARM_SERVICE);
        outerObserver=new ContentObserver(handler){
            @Override public void onChange(boolean self){
                // Apply immediately; restart the timeout if the panel is currently lit.
                if(closed() && lit())light();
                refresh();
            }
        };
        for(String key:OUTER_KEYS)
            getContentResolver().registerContentObserver(android.provider.Settings.Global.getUriFor(key),false,outerObserver);''')
    s = sub(s, '        inputRunning=false;sideHeld=false;handler.removeCallbacks(longSide);stopMovie();',
            '        getContentResolver().unregisterContentObserver(outerObserver);\n'
            '        inputRunning=false;sideHeld=false;handler.removeCallbacks(longSide);stopMovie();')
    p.write_text(s)


# ------------------------------------------------------------------ native renderer
C_UI = r'''/* KYF37_OUTER_SETTINGS */
static int g_size=2,g_fmt12=0,g_seconds=0,g_batt=3,g_mascot=1,g_second=0;
void kyf37_subdisplay_configure(int size,int fmt12,int seconds,int battery,int mascot,int second) {
 g_size=size<0?0:(size>2?2:size);g_fmt12=fmt12?1:0;g_seconds=seconds?1:0;
 g_batt=battery<0?0:(battery>3?3:battery);g_mascot=mascot?1:0;
 g_second=second<0?0:(second>59?59:second);
}
static void glyph(unsigned char *p,const unsigned char *rows,int w,int h,int x,int y) {
 for(int r=0;r<h;r++)for(int c=0;c<w;c++)if(rows[r]&(1<<(w-1-c)))pixel(p,x+c,y+r);
}
static const unsigned char glyph_a[5]={2,5,7,5,5},glyph_p[5]={6,5,6,4,4},glyph_m[5]={5,7,7,5,5},glyph_pct[5]={17,2,4,8,17};
/* Clock + battery. Occupies x<96 (the mascot owns x>=96); size 3 with battery equals the original layout. */
static void draw_clock_ui(unsigned char *p,int hour,int minute,int battery) {
 int s=g_size+1,h=hour,pm=0;
 if(g_fmt12){pm=hour>=12;h=hour%12;if(!h)h=12;}
 int top=g_batt?(s==3?2:(27-7*s)/2):(36-7*s)/2;
 int w=5*s,gap=s,cs=s>1?2:1,x=2;
 if(!g_fmt12 || h>=10)digit(p,h/10,x,top,s);
 x+=w+gap;digit(p,h%10,x,top,s);
 int cx=x+w+gap+1,dy1=5*s/3,dy2=14*s/3;
 for(int yy=0;yy<s;yy++)for(int xx=0;xx<cs;xx++){pixel(p,cx+xx,top+dy1+yy);pixel(p,cx+xx,top+dy2+yy);}
 int mx=cx+cs+2*gap;
 digit(p,minute/10,mx,top,s);digit(p,minute%10,mx+w+gap,top,s);
 int tail=mx+2*w+gap+3,marker=tail;
 if(g_seconds){
  digit(p,g_second/10,tail,top+7*s-7,1);digit(p,g_second%10,tail+6,top+7*s-7,1);
  if(s<3)marker=tail+13;
 }
 if(g_fmt12){glyph(p,pm?glyph_p:glyph_a,3,5,marker,top);glyph(p,glyph_m,3,5,marker+4,top);}
 if(g_batt) {
  int icon=g_batt&1,pct=g_batt&2;
  if(icon) {
   for(int bx=3;bx<=18;bx++){pixel(p,bx,29);pixel(p,bx,34);}
   for(int by=29;by<=34;by++){pixel(p,3,by);pixel(p,18,by);}
   pixel(p,19,31);pixel(p,19,32);
   for(int bx=5;bx<5+12*battery/100;bx++)for(int by=31;by<=32;by++)pixel(p,bx,by);
  }
  if(pct) {
   int bx=icon?(battery<100?32:26):3;
   if(battery==100){digit(p,1,bx,27,1);bx+=6;}
   digit(p,(battery/10)%10,bx,27,1);digit(p,battery%10,bx+6,27,1);
   glyph(p,glyph_pct,5,5,bx+13,28);
  }
 }
}
'''

JNI = r'''
/* KYF37_OUTER_SETTINGS */
JNIEXPORT void JNICALL Java_org_kyf37_subdisplay_OuterScreenService_configure(
    JNIEnv *env,jclass type,jint size,jint fmt12,jint seconds,jint battery,jint mascot,jint second) {
    (void)env;(void)type;
    kyf37_subdisplay_configure(size,fmt12,seconds,battery,mascot,second);
}
'''


def patch_native():
    r = APP / 'render.c'
    s = r.read_text()
    if MARK not in s:
        pat = re.compile(r'/\* Large 21px-high clock; the battery is a compact footer\. \*/\n.*?'
                         r'digit\(p,\(battery/10\)%10,32,27,1\);digit\(p,battery%10,38,27,1\);\n', re.S)
        assert pat.search(s), 'idle clock block not found'
        s = pat.sub('draw_clock_ui(p,hour,minute,battery);\n', s, count=1)
        old = (' int id=scene_start[0]+(phase&1)%scene_count[0];\n'
               ' pose(p,id,106,34-pet_poses[id].h+(phase&1),1);\n'
               ' if((phase&3)==2)sparkle(p,123,13,1);\n')
        s = sub(s, old, ' if(g_mascot){\n' + old + ' }\n')
        s = sub(s, 'int kyf37_subdisplay_idle(unsigned char *p,', C_UI + 'int kyf37_subdisplay_idle(unsigned char *p,')
        r.write_text(s)
    h = APP / 'render.h'
    s = h.read_text()
    if 'kyf37_subdisplay_configure' not in s:
        h.write_text(s + '\nvoid kyf37_subdisplay_configure(int size,int fmt12,int seconds,int battery,int mascot,int second);\n')
    c = APP / 'controller.c'
    s = c.read_text()
    if '/* ' + MARK + ' */' in s:
        s = s[:s.index('\n/* ' + MARK + ' */')]
    c.write_text(s + JNI)
    mirror = W.parent / 'kyf37-rom/navigation/subdisplay'
    if mirror.exists():
        for name in ('render.c', 'render.h', 'controller.c'):
            shutil.copyfile(APP / name, mirror / name)


# ------------------------------------------------------------------ settings UI
def patch_ui():
    if not PHONE.exists():
        print('Kyf37PhoneSettings missing: skipping UI')
        return
    shutil.copyfile(W / 'Kyf37OuterScreenSettings.java.txt', PHONE / 'src/org/kyf37/phonesettings/OuterScreenSettings.java')
    pm = PHONE / 'AndroidManifest.xml'
    s = pm.read_text()
    if '.OuterScreenSettings' not in s:
        s = sub(s, '    </application>', '        <activity android:name=".OuterScreenSettings" android:label="Outer screen" android:exported="true" />\n    </application>')
        pm.write_text(s)
    for p in (PHONE / 'src/org/kyf37/phonesettings/PhoneSettings.java', W / 'Kyf37PhoneSettings.java.txt'):
        s = p.read_text()
        if 'case 15:' in s:
            continue
        s = sub(s, '"About phone", "Appearance" };', '"About phone", "Appearance", "Outer screen" };')
        s = sub(s, 'R.drawable.ic_pastel_settings};', 'R.drawable.ic_pastel_settings, R.drawable.ic_pastel_clock};')
        s = sub(s, 'R.drawable.sky_settings};', 'R.drawable.sky_settings, R.drawable.sky_clock};')
        s = sub(s, '                case 14: return Settings.Global',
                '                case 15: { int t = Settings.Global.getInt(getContentResolver(),"kyf37_outer_timeout",10); '
                'return t == 0 ? "Always on" : (t >= 60 ? (t / 60) + " min" : t + " s"); }\n'
                '                case 14: return Settings.Global')
        s = sub(s, '                case 14: startActivity(new Intent(PhoneSettings.this,AppearanceSettings.class)); break;',
                '                case 14: startActivity(new Intent(PhoneSettings.this,AppearanceSettings.class)); break;\n'
                '                case 15: startActivity(new Intent(PhoneSettings.this,OuterScreenSettings.class)); break;')
        p.write_text(s)
    top = SETTINGS / 'res/xml/top_level_settings.xml'
    if top.exists():
        s = top.read_text()
        if 'kyf37_outer_screen' not in s:
            s = sub(s, '</PreferenceScreen>', '''    <Preference android:key="kyf37_outer_screen" android:title="Outer screen"
        android:summary="Clock, battery, timeout, animations" android:order="-78" android:icon="@drawable/ic_settings_all">
        <intent android:targetPackage="org.kyf37.phonesettings" android:targetClass="org.kyf37.phonesettings.OuterScreenSettings" />
    </Preference>
</PreferenceScreen>''')
            top.write_text(s)


if __name__ == '__main__':
    patch_service()
    patch_native()
    patch_ui()
    print('Outer screen settings: timeout (default 10 s), size/format/seconds/battery/animation/Bad Apple via Settings.Global kyf37_outer_*')
