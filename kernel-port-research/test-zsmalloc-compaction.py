"""Execute the actual backported allocator on ARM32 with modeled kernel primitives."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
test = work / 'host-tests/zsmalloc'
test.mkdir(parents=True, exist_ok=True)
source = (work / 'kernel/drivers/staging/zsmalloc/zsmalloc-main.c').read_text()
source = re.sub(r'^#include .+$', '', source, flags=re.M)
harness = (root / 'zsmalloc-test-shim.h').read_text() + '\n' + source + r'''
static unsigned long handles[1000];
static unsigned int sizes[1000];
static unsigned long results[5][3];
static unsigned int seed=8909;
static unsigned int random_u32(void) { seed=seed*1664525U+1013904223U;return seed; }
static unsigned char pattern(int index,int pos) { return (index*17+pos*31+7)&255; }
static void fill(struct zs_pool *p,int i) {
    unsigned char *bytes=zs_map_object(p,handles[i],ZS_MM_WO);
    unsigned int j;for(j=0;j<sizes[i];j++)bytes[j]=pattern(i,j);
    zs_unmap_object(p,handles[i]);
}
static void verify(struct zs_pool *p,int i) {
    unsigned char *bytes=zs_map_object(p,handles[i],ZS_MM_RO);
    unsigned int j;for(j=0;j<sizes[i];j++)if(bytes[j]!=pattern(i,j))stop(20);
    zs_unmap_object(p,handles[i]);
}
static void balanced(void) { if(held_locks || mappings || preemptions || faults)stop(21); }
static void run(int mode) {
    struct zs_pool *p=zs_create_pool(GFP_KERNEL);
    unsigned long before,after,moved;
    int i,round;
    trace('0'+mode);
    if(!p)stop(22);
    if(zs_malloc(p,0) || zs_malloc(p,4097))stop(23);
    for(i=0;i<1000;i++) {
        sizes[i]=mode==0?128:mode==1?1024:mode==2?2047:mode==3?4096:1+random_u32()%4096;
        handles[i]=zs_malloc(p,sizes[i]);if(!handles[i])stop(24);fill(p,i);
    }
    for(i=0;i<1000;i++)if(i%4!=0) { zs_free(p,handles[i]);handles[i]=0; }
    before=zs_get_total_pages(p);
    trace('a');
    if(zs_get_total_size_bytes(p)!=((u64)before<<PAGE_SHIFT))stop(25);
    /* A held handle is skipped; compaction must preserve its location/data. */
    pin_tag(handles[0]);
    moved=zs_compact(p);
    trace('b');
    unpin_tag(handles[0]);
    after=zs_get_total_pages(p);
    results[mode][0]=before;results[mode][1]=after;results[mode][2]=moved;
    if(after>before)stop(26);
    if(mode<3 && (!moved || after>=before))stop(27);
    for(i=0;i<1000;i++)if(handles[i])verify(p,i);
    for(round=0;round<3;round++) {
        zs_compact(p);
        for(i=0;i<1000;i++)if(handles[i]) {
            /* exercise read-write preservation across a partial update */
            unsigned char *bytes=zs_map_object(p,handles[i],ZS_MM_RW);
            bytes[0]=pattern(i,0);zs_unmap_object(p,handles[i]);verify(p,i);
        }
    }
    trace('c');
    fail_allocation=1;
    if(zs_malloc(p,64))stop(28);
    fail_allocation=0;
    for(i=0;i<1000;i++)if(handles[i])zs_free(p,handles[i]);
    if(zs_get_total_pages(p) || live_pages)stop(29);
    zs_compact(p);zs_destroy_pool(p);balanced();
    trace('d');
}
void _start(void) {
    int i;if(zs_init())stop(30);
    for(i=0;i<5;i++)run(i);
    zs_exit();balanced();
    {
        register long r0 __asm__("r0")=1;
        register void *r1 __asm__("r1")=results;
        register long r2 __asm__("r2")=sizeof(results);
        register long r7 __asm__("r7")=4;
        __asm__ volatile("svc 0" : "+r"(r0) : "r"(r1),"r"(r2),"r"(r7) : "memory");
        if(r0!=sizeof(results))stop(31);
    }
    stop(0);
}
'''
(test / 'allocator.c').write_text(harness)
cross = '/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-'
binary = test / 'zsmalloc-arm-test'
subprocess.run([cross + 'gcc', '-O2', '-fno-strict-aliasing', '-fno-stack-protector',
                '-fno-builtin', '-nostdlib', '-static', '-marm', '-march=armv7-a',
                '-Wl,-e,_start', str(test / 'allocator.c'), '-lgcc', '-o', str(binary)], check=True)
result = subprocess.run([str(work / 'host-tools/qemu/usr/bin/qemu-arm'), '-cpu', 'cortex-a7',
                         str(binary)], timeout=60, capture_output=True)
assert result.returncode == 0, f'Allocator harness exit {result.returncode}'
counts = list(struct.iter_unpack('<III', result.stdout))
assert len(counts) == 5
report = {'exit_code': result.returncode, 'architecture': 'ARM32 Cortex-A7 emulation',
          'allocations': 5000, 'workloads': ['128-byte', '1024-byte', '2047-byte', '4096-byte', 'random-size'],
          'checks': ['data retained across compaction', 'fragmented pools shrink', 'pinned handles skipped',
                     'mapping/lock balance', 'RO/WO/RW mapping modes', 'allocation failure',
                     'invalid allocation sizes', 'all pages released', 'original byte-count API'],
          'allocator_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
          'modeled_fragmented_pool_results': [dict(pages_before=a,pages_after=b,objects_moved=c)
                                             for a,b,c in counts],
          'physical_phone_access': False,
          'limitation': 'Actual allocator with modeled pages, slab, one CPU and locks; not kernel concurrency or OOM validation.'}
(root / 'zsmalloc-compaction-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(report)
