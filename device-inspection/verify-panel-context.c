#include <selinux/selinux.h>
#include <selinux/label.h>
#include <sys/stat.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 struct selinux_opt option={SELABEL_OPT_PATH,argv[1]};
 struct selabel_handle *handle=selabel_open(SELABEL_CTX_FILE,&option,1);
 if(!handle){perror("selabel_open");return 2;}
 const char *paths[]={"/dev/graphics/fb0","/dev/graphics/fb1"};
 const char *expected[]={"u:object_r:graphics_device:s0","u:object_r:kyf37_subdisplay_device:s0"};
 for(int i=0;i<2;i++) {
  char *context=NULL;
  if(selabel_lookup(handle,&context,paths[i],S_IFCHR))return 3;
  printf("%s %s\n",paths[i],context);
  int matches=!strcmp(context,expected[i]);freecon(context);
  if(!matches)return 1;
 }
 selabel_close(handle);return 0;
}
