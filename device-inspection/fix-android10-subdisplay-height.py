from pathlib import Path
root=Path('/home/pablo/kyf37-android10/packages/apps/Kyf37OuterScreen')
for f in ['controller.c','framebuffer.c','render.c']:
 p=root/f;s=p.read_text().replace('128*72','128*36').replace('var.yres!=72','var.yres!=36').replace('y<72','y<36')
 if f=='render.c':
  a=s.index(' digit(p,hour/10,');b=s.index(' return 0;',a)
  s=s[:a]+''' digit(p,hour/10,20,2,3);digit(p,hour%10,38,2,3);
 for(int dy=0;dy<3;dy++) for(int dx=0;dx<3;dx++) {
  pixel(p,61+dx,7+dy);pixel(p,61+dx,16+dy);
 }
 digit(p,minute/10,73,2,3);digit(p,minute%10,91,2,3);
 for(int x=20;x<=56;x++) {pixel(p,x,26);pixel(p,x,35);}
 for(int y=26;y<=35;y++) {pixel(p,20,y);pixel(p,56,y);}
 for(int y=29;y<=32;y++) {pixel(p,57,y);pixel(p,58,y);}
 int width=33*battery/100;
 for(int y=28;y<=33;y++) for(int x=22;x<22+width;x++) pixel(p,x,y);
 if(battery==100) digit(p,1,77,28,1);
 digit(p,(battery/10)%10,83,28,1);digit(p,battery%10,89,28,1);
 pixel(p,96,28);pixel(p,98,34);
 for(int i=0;i<7;i++) pixel(p,99-i/2,28+i);
'''+s[b:]
 p.write_text(s)
 host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/navigation/subdisplay')/f
 host.write_text(s)
print('Corrected physical panel128x36;128x72 is double framebuffer allocation, not screen resolution')
