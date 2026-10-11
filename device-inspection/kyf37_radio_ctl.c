/* NAS read through the firmware's QMUX daemon; no radio configuration writes. */
#include <errno.h>
#include <stdint.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
struct hdr {int msg,client;uint32_t txn;int sys_err,qmi_err,conn,service;uint8_t cid,flags;uint16_t pad;};
static int fd,client;static uint32_t txn=1;
static int receive(unsigned char *buf){int n,total;if(recv(fd,&total,4,MSG_WAITALL)!=4)return -1;if(total<8||total>8192)return -2;memcpy(buf,&total,4);n=recv(fd,buf+4,total-4,MSG_WAITALL);return n==total-4?total:-3;}
static int sendmsgq(int msg,int service,int cid,unsigned char *data,int size){
 unsigned char packet[8192]={0};int total=8+sizeof(struct hdr)+size;memcpy(packet,&total,4);memcpy(packet+4,&client,4);
 struct hdr h={0};h.msg=msg;h.client=client;h.txn=txn++;h.service=service;h.cid=cid;
 memcpy(packet+8,&h,sizeof(h));memcpy(packet+8+sizeof(h),data,size);
 return send(fd,packet,total,MSG_NOSIGNAL)==total?0:-1;
}
static int control(int msg,unsigned char *payload,unsigned char *out){
 if(sendmsgq(msg,0,0,payload,864)<0)return -1;
 for(int i=0;i<20;i++){int n=receive(out);if(n<0)return n;struct hdr *h=(void*)(out+8);
 printf("control_reply msg=%d txn=%u sys=%d qmi=%d bytes=%d\n",h->msg,h->txn,h->sys_err,h->qmi_err,n);
 if(h->msg==msg){if(h->sys_err||h->qmi_err)return -4;return n;}}
 return -5;
}
static uint64_t getmask(unsigned char *p,int n){
 for(int i=7;i+3<=n;){int type=p[i],len=p[i+1]|p[i+2]<<8;i+=3;
 if(i+len>n)break;if(type==0x15&&len==8){uint64_t mask;memcpy(&mask,p+i,8);return mask;}i+=len;}
 return 0;
}
static int roundtrip(int cid,unsigned char *req,int len,unsigned char *out){
 if(sendmsgq(0,3,cid,req,len)<0)return -1;
 for(int i=0;i<20;i++){int n=receive(out);if(n<0)return -2;struct hdr *h=(void*)(out+8);
 unsigned char *p=out+40;int size=n-40;
 printf("NAS_reply hex=");for(int j=0;j<size;j++)printf("%02x",p[j]);puts("");
 if(h->msg==0&&h->service==3&&size>=7&&p[0]==2&&p[3]==req[3]&&p[4]==req[4])return size;
 }return -3;
}

/* Well-formed QMI request on an arbitrary service. Frame = [flags=0][txn lo][txn hi][msgid lo][msgid hi][len lo][len hi][TLVs];
   sent at QMUX level as msg type 0 (service request) like kyf37_qmux.c does. Returns reply payload size or <0.
   (An earlier version passed the QMI message id as the QMUX msg type with an empty body: every non-NAS-0x34 probe was malformed.) */
static int svc_roundtrip(int service,int cid,int msgid,unsigned char *tlv,int tlvlen,unsigned char *out){
 static unsigned short tx=100; unsigned char f[512]; unsigned short t=tx++,L=(unsigned short)tlvlen;
 f[0]=0;f[1]=t&255;f[2]=t>>8;f[3]=msgid&255;f[4]=msgid>>8;f[5]=L&255;f[6]=L>>8; if(tlvlen>0)memcpy(f+7,tlv,tlvlen);
 if(sendmsgq(0,service,cid,f,7+tlvlen)<0)return -1;
 for(int i=0;i<20;i++){int n=receive(out);if(n<0){printf("svc %d msg 0x%x receive failed n=%d errno=%d%c",service,msgid,n,errno,10);return -2;}struct hdr *h=(void*)(out+8);
  unsigned char *p=out+40;int size=n-40;
  if(h->msg==0&&h->service==service&&size>=7&&p[0]==2&&p[3]==(msgid&255)&&p[4]==(msgid>>8))return size;
 }return -3;
}
static void dump(const char *tag,unsigned char *p,int n){printf("%s hex=",tag);for(int j=0;j<n;j++)printf("%02x",p[j]);puts("");}
int main(int argc,char **argv){
 setbuf(stdout,NULL);if(setgid(1001)||setuid(1001)){perror("radio credentials");return 1;}
 fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0){perror("socket");return 1;}
 struct sockaddr_un local={0};local.sun_family=AF_UNIX;
 snprintf(local.sun_path,sizeof(local.sun_path),"/dev/socket/qmux_radio/qmux_client_socket%7d",getpid());
 unlink(local.sun_path);if(bind(fd,(void*)&local,sizeof(local))<0){perror("bind");return 1;}
 chmod(local.sun_path,0660);
 struct timeval timeout={10,0};setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
 struct sockaddr_un addr={0};addr.sun_family=AF_UNIX;strcpy(addr.sun_path,"/dev/socket/qmux_radio/qmux_connect_socket");
 if(connect(fd,(void*)&addr,sizeof(addr))<0){perror("connect");return 2;}
 if(recv(fd,&client,4,MSG_WAITALL)!=4){perror("client id");return 3;}
 unsigned char payload[864]={0},out[8192];memcpy(payload,&client,4);
 if(control(4,payload,out)<0)return 4;
 /* DMS client (service 2) */
 memset(payload,0,sizeof(payload));payload[0]=2;
 if(control(1,payload,out)<0)return 5;
 int dms=out[8+sizeof(struct hdr)];printf("DMS_client=%d\n",dms);
 unsigned char r[8192];
 int n=svc_roundtrip(2,dms,0x2d,(unsigned char[]){0},0,r); /* GET operating mode */
 if(n>=0){dump("DMS_get_mode",r+40,n);}
 /* read-only: DMS Get Band Capability (0x45): TLV 0x10 = 2G/3G band mask, TLV 0x11 = LTE band mask (u64 bit n-1 = band n) */
 n=svc_roundtrip(2,dms,0x45,(unsigned char[]){0},0,r); if(n>=0)dump("DMS_band_capability",r+40,n); else printf("DMS_band_capability err=%d%c",n,10);
 if(argc>=2&&!strcmp(argv[1],"--mode-cycle")){
   unsigned char lpm[]={1,1,0,1}; /* TLV 0x01: operating mode 1 = low power */
   n=svc_roundtrip(2,dms,0x2e,lpm,4,r); if(n>=0)dump("DMS_set_LPM",r+40,n); else printf("DMS_set_LPM err=%d\n",n);
   sleep(2);
   unsigned char onl[]={1,1,0,0}; /* operating mode 0 = online */
   n=svc_roundtrip(2,dms,0x2e,onl,4,r); if(n>=0)dump("DMS_set_ONLINE",r+40,n); else printf("DMS_set_ONLINE err=%d\n",n);
   sleep(5);
   n=svc_roundtrip(2,dms,0x2d,(unsigned char[]){0},0,r); if(n>=0)dump("DMS_get_mode_after",r+40,n);
 }
 /* NAS client */
 memset(payload,0,sizeof(payload));payload[0]=3;
 if(control(1,payload,out)<0)return 6;
 int cid=out[8+sizeof(struct hdr)];printf("NAS_client=%d\n",cid);
 /* read-only: NAS Get Serving System (0x0024) and Get Operating Mode dump */
 n=svc_roundtrip(3,cid,0x24,(unsigned char[]){0},0,r); if(n>=0)dump("NAS_serving_system",r+40,n); else printf("NAS_serving_system err=%d\n",n);
 /* read-only: UIM (service 11) Get Card Status 0x2f, to see whether a SIM/UIM service is running */
 memset(payload,0,sizeof(payload));payload[0]=11;
 if(control(1,payload,out)>=0){int uim=out[8+sizeof(struct hdr)];printf("UIM_client=%d\n",uim);
  n=svc_roundtrip(11,uim,0x2f,(unsigned char[]){0},0,r); if(n>=0)dump("UIM_card_status",r+40,n); else printf("UIM_card_status err=%d\n",n);}
 unsigned char nas[]={0,1,0,0x34,0,0,0};int nn=roundtrip(cid,nas,sizeof(nas),out);
 if(nn<0)return 7;uint64_t mask=getmask(out+40,nn);printf("original_LTE_mask=0x%016llx\n",(unsigned long long)mask);
 int do_spain=(argc>=2&&!strcmp(argv[argc-1],"--enable-spain"));
 int do_set=(argc>=3&&!strcmp(argv[argc-2],"--set-lte"));
 if(do_spain||do_set){
   uint64_t desired=do_set?strtoull(argv[argc-1],0,16):(mask|(1ULL<<2)|(1ULL<<6)|(1ULL<<7)|(1ULL<<19)|(1ULL<<27));
   unsigned char set[]={0,2,0,0x33,0,15,0,0x15,8,0,0,0,0,0,0,0,0,0,0x17,1,0,1};
   memcpy(set+10,&desired,8);printf("requested_LTE_mask=0x%016llx\n",(unsigned long long)desired);
   nn=roundtrip(cid,set,sizeof(set),out);if(nn<0)return 8;
   nas[1]=3;nn=roundtrip(cid,nas,sizeof(nas),out);if(nn<0)return 9;
   uint64_t readback=getmask(out+40,nn);printf("readback_LTE_mask=0x%016llx\n",(unsigned long long)readback);
 }
 close(fd);return 0;
}
