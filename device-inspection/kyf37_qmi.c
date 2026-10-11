/* Read-only NAS preference query through Qualcomm's legacy IPC router. */
#include <stdint.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <poll.h>
#include <errno.h>
#include "msm_ipc.h"
int main(void) {
    int fd=socket(AF_MSM_IPC,SOCK_DGRAM,0);
    if(fd<0){perror("socket");return 1;}
    unsigned char lookup[sizeof(struct server_lookup_args)+16*sizeof(struct msm_ipc_server_info)]={0};
    struct server_lookup_args *a=(void*)lookup;
    a->port_name.service=3;a->port_name.instance=1;
    a->lookup_mask=0xff;a->num_entries_in_array=16;
    int ret=ioctl(fd,IPC_ROUTER_IOCTL_LOOKUP_SERVER,a);
    printf("lookup_ret=%d errno=%d found=%d\n",ret,errno,a->num_entries_found);
    if(ret<0||a->num_entries_found<1)return 2;
    for(int i=0;i<a->num_entries_found&&i<16;i++)
      printf("server node=%u port=%u service=%u instance=%u\n",a->srv_info[i].node_id,a->srv_info[i].port_id,a->srv_info[i].service,a->srv_info[i].instance);
    struct sockaddr_msm_ipc addr={0};addr.family=AF_MSM_IPC;addr.address.addrtype=MSM_IPC_ADDR_ID;
    addr.address.addr.port_addr.node_id=a->srv_info[0].node_id;
    addr.address.addr.port_addr.port_id=a->srv_info[0].port_id;
    unsigned char request[]={0,1,0,0x34,0,0,0};
    if(sendto(fd,request,sizeof(request),0,(void*)&addr,sizeof(addr))<0){perror("sendto");return 3;}
    struct pollfd p={fd,POLLIN,0};
    for(int i=0;i<10;i++) {
      if(poll(&p,1,1000)<=0)continue;
      unsigned char response[8192];int n=recv(fd,response,sizeof(response),0);
      printf("response_bytes=%d hex=",n);
      for(int j=0;j<n;j++)printf("%02x",response[j]);puts("");
      if(n>=7&&response[0]==2&&response[1]==1&&response[3]==0x34){close(fd);return 0;}
    }
    puts("No matching NAS response");close(fd);return 4;
}
