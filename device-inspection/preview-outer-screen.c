#include "render.h"
#include <stdio.h>
#include <assert.h>
#include <string.h>
int main(void) {
    unsigned char guarded[128*72+2];
    memset(guarded,0xaa,sizeof guarded);
    assert(kyf37_subdisplay_clock(guarded+1,128*72,24,0,50)==-1);
    assert(kyf37_subdisplay_clock(guarded+1,128*72,12,60,50)==-1);
    assert(kyf37_subdisplay_clock(guarded+1,128*72,12,0,101)==-1);
    assert(kyf37_subdisplay_clock(guarded+1,128*72,14,37,72)==0);
    assert(guarded[0]==0xaa && guarded[sizeof guarded-1]==0xaa);
    printf("P5\n128 72\n255\n");
    for(unsigned i=1;i<sizeof guarded-1;i++) {
        assert(guarded[i]<=1);
        putchar(guarded[i] ? 255 : 0);
    }
    return 0;
}
