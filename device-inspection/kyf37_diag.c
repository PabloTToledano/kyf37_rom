/* Capture modem F3 debug messages over /dev/diag (memory-device mode). usage: kyf37_diag <seconds> */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <poll.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <time.h>
#define DIAG_IOCTL_SWITCH_LOGGING 7
#define MEMORY_DEVICE_MODE 2
#define USER_SPACE_DATA_TYPE 0x20
static void send_cmd(int fd, const unsigned char *pkt, int len){
  unsigned char buf[256]; int t=USER_SPACE_DATA_TYPE; memcpy(buf,&t,4); memcpy(buf+4,pkt,len);
  int n=write(fd,buf,len+4); printf("write cmd %02x %02x -> %d (errno %d)\n",pkt[0],pkt[1],n,n<0?errno:0);
}
int main(int argc,char **argv){
  int secs=argc>1?atoi(argv[1]):20; setbuf(stdout,NULL);
  int fd=open("/dev/diag",O_RDWR|O_NONBLOCK); if(fd<0){perror("open /dev/diag");return 1;}
  int mode=MEMORY_DEVICE_MODE; int r=ioctl(fd,DIAG_IOCTL_SWITCH_LOGGING,&mode); printf("switch_logging ret=%d errno=%d\n",r,r<0?errno:0);
  unsigned char all_msg[]={0x7d,0x05,0x00,0x00,0xff,0xff,0xff,0xff};
  send_cmd(fd,all_msg,sizeof(all_msg));
  static unsigned char buf[65536]; time_t end=time(0)+secs; long total=0; FILE *raw=fopen("/data/local/tmp/diag_raw.bin","wb");
  while(time(0)<end){
    int n=read(fd,buf,sizeof(buf));
    if(n<=0){ usleep(100000); continue; }
    total+=n; if(raw){ fwrite(buf,1,n,raw); fflush(raw); }
    int i=0; while(i<n){ int j=i; while(j<n&&buf[j]>=0x20&&buf[j]<0x7f) j++; if(j-i>=6){ fwrite(buf+i,1,j-i,stdout); putchar(10); fflush(stdout);} i=(j>i)?j:i+1; }
  }
  printf("done total_bytes=%ld\n",total); if(raw) fclose(raw); return 0;
}
