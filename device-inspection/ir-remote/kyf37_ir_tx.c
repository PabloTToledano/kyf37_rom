/* Root command-line transmitter, no daemon. GPL-2.0-only. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <termios.h>
#include <signal.h>
#ifdef __ANDROID__
#include <sys/system_properties.h>
#include <dirent.h>
#endif
#include "kyf37_ir_uapi.h"
static volatile sig_atomic_t interrupted;
static void stop_requested(int signum) { (void)signum; interrupted=1; }
#ifdef __ANDROID__
/* The legacy daemon can hang in felicadev_open on this ROM. Stop it before
 * a direct reservation, and reject any other live user of either device. */
static int direct_reserve(void) {
 char state[PROP_VALUE_MAX],path[128],target[256];DIR *proc,*fds;struct dirent *p,*f;int fd,ret=-1;unsigned i;unsigned char reserve=1;
 if(__system_property_set("ctl.stop","kflcd"))return -1;
 for(i=0;i<100;i++){__system_property_get("init.svc.kflcd",state);if(!strcmp(state,"stopped"))break;usleep(20000);}
 if(i==100)goto restore;
 proc=opendir("/proc");if(!proc)goto restore;
 while((p=readdir(proc))){
  if(p->d_name[0]<'0'||p->d_name[0]>'9')continue;
  if(snprintf(path,sizeof(path),"/proc/%s/fd",p->d_name)>=(int)sizeof(path)){closedir(proc);goto restore;}
  fds=opendir(path);if(!fds){if(errno==ENOENT)continue;closedir(proc);goto restore;}
  while((f=readdir(fds))){ssize_t n;
   if(f->d_name[0]=='.')continue;
   if(snprintf(path,sizeof(path),"/proc/%s/fd/%s",p->d_name,f->d_name)>=(int)sizeof(path)){closedir(fds);closedir(proc);goto restore;}
   n=readlink(path,target,sizeof(target)-1);if(n<0){if(errno==ENOENT)continue;closedir(fds);closedir(proc);goto restore;}target[n]=0;
   if(!strcmp(target,"/dev/ttyHSL3")||!strcmp(target,"/dev/felica")){closedir(fds);closedir(proc);goto restore;}
  }closedir(fds);
 }closedir(proc);
 fd=open("/dev/felica_ue",O_WRONLY|O_CLOEXEC);if(fd<0)goto restore;
 if(write(fd,&reserve,1)==1)ret=0;close(fd);
 if(!ret)return 0;
restore: __system_property_set("ctl.start","kflcd");return -1;
}
static void direct_release(void){unsigned char reserve=0;int fd=open("/dev/felica_ue",O_WRONLY|O_CLOEXEC);if(fd>=0){write(fd,&reserve,1);close(fd);}__system_property_set("ctl.start","kflcd");}
#endif
static int exchange(unsigned char cmd) {
 struct sockaddr_un a={.sun_family=AF_UNIX};
 unsigned char req[8]={0}, res[8]; size_t n=0; int fd, result=-1;
 struct timeval timeout={2,0};
 strcpy(a.sun_path,"/dev/socket/kflcd"); req[0]=cmd;
 fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0); if(fd<0)return -1;
 setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
 setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
 if(connect(fd,(void*)&a,sizeof(a)) || write(fd,req,8)!=8)goto out;
 while(n<8){ssize_t got=read(fd,res+n,8-n);if(got<=0)goto out;n+=got;}
 result=(int)((uint32_t)res[4]|((uint32_t)res[5]<<8)|((uint32_t)res[6]<<16)|((uint32_t)res[7]<<24));
 if(getenv("KYF37_IR_DEBUG")){unsigned char extra[4]={0};int got=recv(fd,extra,4,MSG_DONTWAIT);fprintf(stderr,"kflcd cmd=%02x reply=%02x%02x%02x%02x %02x%02x%02x%02x extra(%d)=%02x%02x%02x%02x status=%d\n",cmd,res[0],res[1],res[2],res[3],res[4],res[5],res[6],res[7],got,extra[0],extra[1],extra[2],extra[3],result);}
out: if(result<0 && getenv("KYF37_IR_DEBUG"))perror("kflcd exchange"); close(fd); return result;
}
int main(int argc,char **argv) {
 struct kyf37_ir_request r={0}; int lock=-1,tty=-1,backend=-1,gate=-1,owned=0,rc=1,saved=0,arbitration;
 struct sigaction sa; memset(&sa,0,sizeof(sa));sa.sa_handler=stop_requested;
 sigaction(SIGTERM,&sa,NULL);sigaction(SIGINT,&sa,NULL);signal(SIGPIPE,SIG_IGN);
 if(argc!=2 || (strcmp(argv[1],"probe") && strcmp(argv[1],"send") && strcmp(argv[1],"validate"))){fprintf(stderr,"usage: kyf37_ir_tx probe|send|validate (frequency count flags durations on stdin)\n");return 2;}
 if(strcmp(argv[1],"probe")){
  uint64_t total=0; unsigned i;
  if(scanf("%u %u %u",&r.frequency,&r.count,&r.flags)!=3 || r.frequency<30000 || r.frequency>60000 || !r.count || r.count>KYF37_IR_MAX || r.flags>3)goto invalid;
  for(i=0;i<r.count;i++){
   if(scanf("%u",&r.duration[i])!=1 || !r.duration[i] || r.duration[i]>100000 || (!(i&1)&&r.duration[i]>10000))goto invalid;
   total+=r.duration[i];
  }
  if(total>400000)goto invalid;
  if(!strcmp(argv[1],"validate")){printf("VALID frequency=%u count=%u total_us=%llu flags=%u ABI_size=%zu\n",r.frequency,r.count,(unsigned long long)total,r.flags,sizeof(r));return 0;}
 }
 if(getuid()!=0){fprintf(stderr,"Root permission required\n");return 3;}
 lock=open("/data/local/tmp/kyf37-ir-tx.lock",O_CREAT|O_RDWR|O_CLOEXEC|O_NOFOLLOW,0600);
 if(lock<0 || flock(lock,LOCK_EX|LOCK_NB)){fprintf(stderr,"IR transmitter busy\n");goto done;}
 arbitration=exchange(0x11);
 if(arbitration==2)owned=1;
#ifdef __ANDROID__
 else if(arbitration<0 && !interrupted && direct_reserve()==0)owned=2;
#endif
 else {fprintf(stderr,"UART arbitration unavailable/busy; nothing transmitted\n");goto done;}
 tty=open("/dev/ttyHSL3",O_RDWR|O_NOCTTY|O_CLOEXEC|O_NONBLOCK);
 if(tty<0){perror("UART open");goto done;}
 backend=tty;
 if(ioctl(backend,KYF37_IR_PROBE)){
  if(errno!=ENOTTY){perror("Consumer IR kernel support");goto done;}
  backend=open("/dev/kyf37_ir",O_RDWR|O_CLOEXEC);
  if(backend<0 || ioctl(backend,KYF37_IR_PROBE)){perror("Consumer IR module support");goto done;}
 }
 if(!strcmp(argv[1],"probe")){puts("GPIO consumer IR backend available; optical output not measured");rc=0;goto done;}
 /* Enable OEM IR routing before holding shutdown gate. Original daemon does this too. */
 if(ioctl(tty,0x5470)){perror("IR route");goto done;}
 if(interrupted){fprintf(stderr,"Transmission cancelled\n");goto done;}
 gate=open("/dev/irdasd",O_RDWR|O_CLOEXEC);if(gate<0){perror("IR enable");goto done;}
 if(ioctl(backend,KYF37_IR_SEND,&r)){perror("Transmit failed (timing/driver)");goto done;}
 puts("Waveform submitted; device response unconfirmed");rc=0;
done:
 saved=errno;
 if(gate>=0)close(gate);
 if(backend>=0 && backend!=tty)close(backend);
 if(tty>=0){ioctl(tty,0x5471);close(tty);}
 if(owned==1 && exchange(0x12)<0){fprintf(stderr,"UART release failed\n");rc=1;}
#ifdef __ANDROID__
 if(owned==2)direct_release();
#endif
 if(lock>=0)close(lock);
 errno=saved; return rc;
invalid: fprintf(stderr,"Invalid or oversized waveform\n");return 2;
}
