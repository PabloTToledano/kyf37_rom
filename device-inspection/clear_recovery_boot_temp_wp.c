/* Clears only TEMPORARY eMMC protection for stock boot and recovery groups.
 * No SET_WRITE_PROT, SWITCH, permanent register, or partition-content write. */
#define main readonly_main
#include "read_emmc_wp.c"
#undef main
int main(int argc,char **argv) {
    if(argc!=2 || strcmp(argv[1],"--clear-boot-recovery-temporary")) return 1;
    int fd=open("/dev/block/mmcblk0",O_RDWR);
    if(fd<0){perror("open");return 2;}
    unsigned char ext[512]={0};
    if(query(fd,8,0,ext,512))return 3;
    unsigned group=ext[224]*ext[221]*1024u;
    uint32_t sectors=ext[212]|ext[213]<<8|ext[214]<<16|ext[215]<<24;
    if(group!=8192 || sectors!=15269888 || ext[175]!=1) return 4;
    /* Ranges are filled from verified GPT geometry by the host generator. */
    const unsigned starts[2]={184320,151552};
    const unsigned ends[2]={217088,184320};
    for(int r=0;r<2;r++) for(unsigned base=starts[r]/group*group;base<ends[r];base+=group) {
        unsigned char buf[8]={0};
        if(query(fd,31,base,buf,8))return 5;
        unsigned type=buf[7]&3;
        if(type>1){fprintf(stderr,"Refusing non-temporary WP at %u type=%u\n",base,type);return 6;}
        if(type==0)continue;
        struct mmc_ioc_cmd c;memset(&c,0,sizeof(c));
        c.opcode=29;c.arg=base;c.write_flag=1;c.flags=413;
        if(ioctl(fd,MMC_IOC_CMD,&c)){perror("clear temporary WP");return 7;}
        if(query(fd,31,base,buf,8) || (buf[7]&3)){fprintf(stderr,"WP readback failed at %u\n",base);return 8;}
        printf("cleared_temporary_wp sector=%u\n",base);
    }
    close(fd);puts("boot_recovery_temporary_wp_clear_verified");return 0;
}
