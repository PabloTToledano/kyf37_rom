#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/mmc/ioctl.h>
/* Read-only eMMC commands: SEND_EXT_CSD (8), SEND_WRITE_PROT_TYPE (31).
 * Never sends SET_WRITE_PROT, CLR_WRITE_PROT, SWITCH, or a write command. */
static int query(int fd, unsigned opcode, unsigned arg, void *buf, unsigned size) {
    struct mmc_ioc_cmd c;
    memset(&c, 0, sizeof(c));
    c.opcode=opcode; c.arg=arg; c.flags=181; c.blksz=size; c.blocks=1;
    mmc_ioc_cmd_set_data(c, buf);
    int r=ioctl(fd, MMC_IOC_CMD, &c);
    if(r) perror("MMC_IOC_CMD read query");
    return r;
}
int main(void) {
    int fd=open("/dev/block/mmcblk0", O_RDONLY);
    if(fd<0) {perror("open");return 1;}
    unsigned char ext[512]={0};
    if(query(fd,8,0,ext,512)) return 2;
    unsigned group=ext[224]*ext[221]*1024u;
    uint32_t sectors=ext[212]|ext[213]<<8|ext[214]<<16|ext[215]<<24;
    printf("revision=%u erase_group_def=%u erase_size=%u wp_size=%u user_wp=0x%02x group_sectors=%u total_sectors=%u\n",ext[192],ext[175],ext[224],ext[221],ext[171],group,sectors);
    if(!ext[175] || !group) return 3;
    for(uint32_t base=0;base<sectors;base+=group*32u) {
        unsigned char buf[8]={0};
        if(query(fd,31,base,buf,8)) return 4;
        uint64_t bits=0;
        for(int i=0;i<8;i++) bits=(bits<<8)|buf[i];
        for(unsigned i=0;i<32 && base+i*group<sectors;i++) {
            unsigned type=(bits>>(i*2))&3;
            printf("sector=%u type=%u\n",base+i*group,type);
        }
    }
    close(fd);return 0;
}
