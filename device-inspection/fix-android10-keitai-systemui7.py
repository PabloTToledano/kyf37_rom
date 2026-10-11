"""Complete keitai header coverage, preserving the notification list offset."""
from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI/res/layout/status_bar_expanded.xml')
s=p.read_text()
old='''        android:id="@+id/keitai_shade_header"
        android:layout_width="match_parent"
        android:layout_height="152dp"
        android:layout_gravity="top"
        android:layout_marginTop="24dp"'''
new='''        android:id="@+id/keitai_shade_header"
        android:layout_width="match_parent"
        android:layout_height="176dp"
        android:layout_gravity="top"
        android:layout_marginTop="0dp"'''
assert old in s or new in s
p.write_text(s.replace(old,new))
print('Keitai header now covers its complete 176dp area')
