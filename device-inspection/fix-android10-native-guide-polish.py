"""Repair the physical F2/F3 positions and modernize app-owned Kyocera guides."""
from pathlib import Path
here = Path(__file__).resolve().parent
p = here/'kyocera-port/Kyf37SoftkeyBridge.java'
s = p.read_text(encoding='utf-8-sig')
s = s.replace('height=Math.round(64*', 'height=Math.round(60*')
# Tonal cells no longer need the six stock background bitmaps in every window.
if '   String[] names={' in s:
    art_start = s.index('   String[] names={')
    art_end = s.index('\n  }',art_start)
    s = s[:art_start]+s[art_end:]
start = s.index('   canvas.drawColor(')
end = s.index('\n  void cell(',start)
s = s[:start]+'''   canvas.drawColor(0xff101722);float left=getWidth()*.36f,right=getWidth()*.64f,half=getHeight()/2f;
   // Physical positions: F1/F2 above the D-pad, F3/F4 below it.
   cell(canvas,1,0,0,left,half,"");cell(canvas,3,0,half,left,getHeight(),"");
   cell(canvas,0,left,0,right,getHeight(),"OK");cell(canvas,2,right,0,getWidth(),half,"");cell(canvas,4,right,half,getWidth(),getHeight(),"");
  }
''' + s[end:]
s = s.replace('String text=key+(label.length()==0?"":" "+label);',
              '''paint.setColor(index==0?0xff29446a:0xff1c2839);
   c.drawRoundRect(new RectF(left+3*d,top+3*d,right-3*d,bottom-3*d),8*d,8*d,paint);
   paint.setColor(s.keys.getEnabled(index)?0xffedf3ff:0xff8294a5);
   String text=label.length()==0?key:label;''')
s = s.replace('paint.setTextSize(11*','paint.setTextSize(12*')
# Reuse the exact printed-key symbols used by the framework guide.
icon = (here/'Kyf37SystemKeyGuide.java.txt').read_text().split('    private void keyIcon(')[1].split('\n    }')[0]
method = '  private void keyIcon('+icon+'\n  }\n'
if 'private void keyIcon(' not in s:
    pos = s.rfind('\n }\n}')
    assert pos >= 0, 'Bar closing brace missing'
    s = s[:pos]+'\n'+method+s[pos:]
if 'keyIcon(c,index,' not in s:
    s = s.replace('String text=label.length()==0?key:label;',
                  'if(index>0)keyIcon(c,index,left+12*d,y,d);\n   x+=index>0?7*d:0;\n   String text=label.length()==0?key:label;')
    s = s.replace('right-left-8*d','right-left-(index>0?30:8)*d')
    s = s.replace('new RectF(left+3*d,y-size/2,left+3*d+size,y+size/2)',
                  'new RectF(right-size-3*d,y-size/2,right-3*d,y+size/2)')
    s = s.replace('x+=size/2;', 'x-=size/2;')
    s = s.replace('right-left-size-10*d','right-left-size-(index>0?30:10)*d')
if p.read_text(encoding='utf-8-sig') != s:
    p.write_text(s,encoding='utf-8')
print('Native guide geometry and tonal appearance staged')
