"""Restore native notifications/QS and keypad mode selection; enlarged standby clock."""
from pathlib import Path
import re
root=Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
here=Path(__file__).resolve().parent
p=root/'res/layout/status_bar_expanded.xml'
s=p.read_text()
s=re.sub(r'    <com.android.systemui.statusbar.phone.Kyf37KeitaiShadeHeader\b.*?/>\s*','',s,flags=re.S)
p.write_text(s)
p=root/'src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java'
s=(here/'Kyf37KeitaiKeys.java.txt').read_text()
s=s.replace('    private ExpandableNotificationRow selected;', '''    private ExpandableNotificationRow selected;
    private boolean quickSettings;
    private View tile;
    private android.graphics.drawable.Drawable tileForeground;
    private void tiles(View view, ArrayList<View> result) {
        if (view.getVisibility()!=View.VISIBLE || view.getAlpha()<0.1f) return;
        if (view instanceof com.android.systemui.plugins.qs.QSTileView) {
            android.graphics.Rect rect=new android.graphics.Rect();
            if(view.getGlobalVisibleRect(rect)) result.add(view);
            return;
        }
        if(view instanceof android.view.ViewGroup){
            android.view.ViewGroup group=(android.view.ViewGroup)view;
            for(int i=0;i<group.getChildCount();i++)tiles(group.getChildAt(i),result);
        }
    }
    private void clearTile(){
        if(tile!=null)tile.setForeground(tileForeground);
        tile=null;tileForeground=null;
    }
    private boolean quickKeys(StatusBarWindowView window,KeyEvent event){
        ArrayList<View> items=new ArrayList<>();
        View frame=window.findViewById(R.id.qs_frame);
        if(frame!=null)tiles(frame,items);
        if(items.isEmpty())return true;
        if(event.getAction()!=KeyEvent.ACTION_DOWN)return true;
        int key=event.getKeyCode(),index=items.indexOf(tile);
        if(index<0)index=0;
        else if(key==KeyEvent.KEYCODE_DPAD_RIGHT||key==KeyEvent.KEYCODE_DPAD_DOWN||key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_UP){
            int[] origin=new int[2];tile.getLocationOnScreen(origin);
            float ox=origin[0]+tile.getWidth()/2f,oy=origin[1]+tile.getHeight()/2f;
            float best=Float.MAX_VALUE;int target=index;
            for(int i=0;i<items.size();i++){
                if(i==index)continue;View candidate=items.get(i);int[] point=new int[2];candidate.getLocationOnScreen(point);
                float dx=point[0]+candidate.getWidth()/2f-ox,dy=point[1]+candidate.getHeight()/2f-oy;
                boolean horizontal=key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT;
                float along=horizontal?dx:dy,across=horizontal?dy:dx;
                if(key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_UP)along=-along;
                if(along<=1)continue;float score=along+4*Math.abs(across);
                if(score<best){best=score;target=i;}
            }
            index=target;
        }
        View next=items.get(index);
        if(next!=tile){
            clearTile();tile=next;tileForeground=tile.getForeground();
            GradientDrawable border=new GradientDrawable();border.setColor(0x302475BB);
            border.setStroke((int)(3*window.getResources().getDisplayMetrics().density),0xffffd35a);
            tile.setForeground(border);
        }
        if(event.getRepeatCount()==0&&(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER))tile.performClick();
        return true;
    }''')
s=s.replace('        int key = event.getKeyCode();','''        int key = event.getKeyCode();
        if(key==KeyEvent.KEYCODE_F2||key==KeyEvent.KEYCODE_MENU){
            if(event.getAction()==KeyEvent.ACTION_DOWN&&event.getRepeatCount()==0){
                quickSettings=!panel.isQsExpanded();clear();clearTile();
                if(quickSettings){
                    panel.expandWithQs();
                    window.postDelayed(()->{
                        if(!panel.isFullyCollapsed()&&panel.isQsExpanded()&&tile==null)
                            quickKeys(window,new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_RIGHT));
                    },500);
                }else panel.expandWithoutQs();
            }
            return true;
        }''',1)
s=s.replace('        NotificationStackScrollLayout stack =', '        if(panel.isQsExpanded())return quickKeys(window,event);\n        NotificationStackScrollLayout stack =',1)
s=s.replace('if (panel == null || panel.isFullyCollapsed()) { clear(); return false; }','if (panel == null || panel.isFullyCollapsed()) { clear(); clearTile(); quickSettings=false; return false; }')
p.write_text(s)
p=root/'src/com/android/systemui/statusbar/phone/Kyf37KeitaiGuide.java'
s=p.read_text().replace('↑↓ Select  ·  OK Open  ·  ←→ Detail  ·  DEL Clear','F2: Quick settings / Notifications  ·  D-pad Select  ·  OK')
p.write_text(s)
p=root/'res-keyguard/layout/keyguard_clock_switch.xml'
s=p.read_text().replace('android:fontFamily="monospace"','android:fontFamily="sans-serif-light"').replace('android:letterSpacing="0.02"','android:letterSpacing="-0.03"')
p.write_text(s)
p=root/'res/values/kyf37_keypad_standby.xml'
p.write_text('<resources><dimen name="widget_big_font_size">76sp</dimen></resources>\n')
# Remove competing original declaration rather than duplicate resource definitions.
for candidate in root.glob('res*/values*/dimens.xml'):
    text=candidate.read_text()
    if candidate.parent.name=='values':
        text=re.sub(r'<dimen name="widget_big_font_size">.*?</dimen>','',text)
        candidate.write_text(text)
    elif candidate.parent.name in ('values-h560dp','values-h650dp'):
        candidate.write_text(re.sub(r'<dimen name="widget_big_font_size">.*?</dimen>', '<dimen name="widget_big_font_size">76sp</dimen>', text))
print('Native notification/QS surface restored; F2 keypad mode and large light clock staged')
