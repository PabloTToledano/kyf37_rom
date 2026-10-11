from pathlib import Path
import subprocess,tempfile
p=Path.home()/'kyf37-android10/external/tinyalsa'
s=(p/'pcm.c').read_text();start=s.index('    /* KYF37 legacy PCM config ABI:');end=s.index('    pcm = calloc',start);block=s[start:end]
code='''#define _GNU_SOURCE
#define __ANDROID__
#include <tinyalsa/asoundlib.h>
#include <string.h>
#include <stddef.h>
#include <assert.h>
#include <sys/mman.h>
#include <unistd.h>
typedef struct { const char *dli_fname; } Dl_info;
static const char *module;
static int dladdr(void *address,Dl_info *info){(void)address;info->dli_fname=module;return 1;}
static struct pcm_config translate(struct pcm_config *config,int *legacy) {
'''+block+'''    *legacy=legacy_config!=NULL;
    return *config;
}
int main(void) {
 _Static_assert(sizeof(struct pcm_config)==40,"Android 10 ABI changed");
 long page=sysconf(_SC_PAGESIZE);
 char *memory=mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
 assert(memory!=MAP_FAILED);assert(mprotect(memory+page,page,PROT_NONE)==0);
 unsigned int *old=(unsigned int*)(memory+page-36);
 unsigned int values[9]={2,48000,960,4,0,240,2147483647,0,240};
 memcpy(old,values,sizeof values);int legacy;
 module="/system/lib/hw/audio.primary.msm8909.so";
 struct pcm_config a=translate((struct pcm_config*)old,&legacy);
 assert(legacy && a.avail_min==240 && a.silence_size==0 && a.period_size==960);
 struct pcm_config modern={.channels=2,.rate=48000,.period_size=240,.period_count=4,.silence_size=128,.avail_min=60};
 module="/system/bin/tinyplay";a=translate(&modern,&legacy);
 assert(!legacy && memcmp(&a,&modern,sizeof a)==0);
 munmap(memory,page*2);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 c=Path(d)/'test.c';exe=Path(d)/'test';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(p/'include'),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: guarded 36-byte stock config translation, zero silence_size, and unchanged modern caller')
