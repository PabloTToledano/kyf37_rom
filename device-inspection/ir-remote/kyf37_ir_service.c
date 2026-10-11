/* Restricted local broker. GPL-2.0-only. Root and platform system UID only. */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
int main(int argc,char **argv) {
 struct sockaddr_un a={.sun_family=AF_UNIX}; int server,client; struct ucred peer;
 const char *path="/dev/socket/kyf37_ir_remote";
 if(getuid()!=0 || argc!=2 || argv[1][0]!='/')return 2;
 signal(SIGPIPE,SIG_IGN);server=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
 if(server<0)return 3;
 strcpy(a.sun_path,path);unlink(path);
 if(bind(server,(void*)&a,sizeof(a)) || chown(path,0,1000) || chmod(path,0660) || listen(server,4))return 4;
 while((client=accept4(server,NULL,NULL,SOCK_CLOEXEC))>=0){
  socklen_t len=sizeof(peer);char mode;struct timeval timeout={4,0};pid_t child;
  setsockopt(client,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
  setsockopt(client,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
  if(getsockopt(client,SOL_SOCKET,SO_PEERCRED,&peer,&len) || (peer.uid!=0 && peer.uid!=1000) || read(client,&mode,1)!=1 || (mode!='P' && mode!='S')){close(client);continue;}
  child=fork();
  if(child==0){dup2(client,0);dup2(client,1);dup2(client,2);close(client);close(server);execl(argv[1],argv[1],mode=='P'?"probe":"send",(char*)NULL);perror("Cannot launch IR transmitter");shutdown(0,SHUT_RD);_exit(127);}
  close(client);if(child>0)waitpid(child,NULL,0);
 }
 close(server);unlink(path);return 0;
}
