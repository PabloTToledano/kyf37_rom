#!/usr/bin/env python3
"""Add a bounded Mametchi-inspired pixel animation on the second side-key press."""
from pathlib import Path
ws = Path(__file__).resolve().parent
app = Path.home() / 'kyf37-android10/packages/apps/Kyf37OuterScreen'
service = app / 'src/org/kyf37/subdisplay/OuterScreenService.java'
service.write_text((ws / 'OuterScreenService-animation.java.txt').read_text())

render = app / 'render.c'
s = render.read_text()
marker = '/* KYF37 bounded star-friend animation */'
if marker in s:
    s = s[:s.index(marker)]
s += (ws / 'outer-animation-render.c.txt').read_text()
render.write_text(s)
(app / 'reference-poses.h').write_text((ws / 'outer-animation/reference-poses.h').read_text())
header = app / 'render.h'
s = header.read_text()
import re
s = re.sub(r'\nint kyf37_subdisplay_(?:animation|idle)[^;]*;', '', s)
header.write_text(s + '\nint kyf37_subdisplay_idle(unsigned char *pixels,size_t count,int hour,int minute,int battery,int phase);\n' + '\nint kyf37_subdisplay_animation(unsigned char *pixels,size_t count,int frame,int hour,int minute,int battery,int scene);\n')
controller = app / 'controller.c'
s = controller.read_text()
marker = '/* KYF37 animation entry: same serialized panel owner */'
if marker in s:
    s = s[:s.index(marker)]
s += '''
/* KYF37 animation entry: same serialized panel owner */
JNIEXPORT jint JNICALL
Java_org_kyf37_subdisplay_OuterScreenService_updateAnimation(
    JNIEnv *env,jclass type,jint frame,jint hour,jint minute,jint battery,jint scene) {
    (void)env;(void)type;
    unsigned char pixels[128*36];
    int result=frame==-1?kyf37_subdisplay_idle(pixels,sizeof pixels,hour,minute,battery,scene):
        kyf37_subdisplay_animation(pixels,sizeof pixels,frame,hour,minute,battery,scene);
    if(result)return -errno;
    int opened=open_panel();
    if(opened)return opened;
    if(!panel_on) {
        if(ioctl(panel_fd,FBIOBLANK,FB_BLANK_UNBLANK))return -errno;
        panel_on=1;
    }
    if(kyf37_subdisplay_commit(panel_fd,pixels,sizeof pixels))return -errno;
    return 0;
}
'''
controller.write_text(s)
mirror = ws.parent / 'kyf37-rom/navigation/subdisplay'
for name in ('render.c','render.h','controller.c','reference-poses.h'):
    (mirror / name).write_text((app / name).read_text())
print('42 shuffled scenes; every press starts a new scene; animated clock idle; opening cancels')

# Keep optional Bad Apple playback when regenerating the animation service.
if (ws.parent / "third-party/bad-apple/assets/badapple.frames.gz").exists():
    import runpy
    runpy.run_path(str(ws / "fix-android10-outer-badapple.py"), run_name="__main__")

# Timeout + persistent options (must run last: it patches the files generated above).
import runpy
runpy.run_path(str(ws / "fix-android10-outer-settings.py"), run_name="__main__")
