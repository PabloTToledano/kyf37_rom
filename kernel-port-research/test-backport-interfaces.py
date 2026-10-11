"""Exercise extracted MemAvailable arithmetic on emulated ARM32 and audit ABI.

No device tools. This does not pretend to boot the kernel or validate entropy.
"""
from pathlib import Path
import json
import random
import re
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
kernel = work / 'kernel'
test = work / 'host-tests/interfaces'
test.mkdir(parents=True, exist_ok=True)
source = (kernel / 'fs/proc/meminfo.c').read_text()
a = source.index('\tfor_each_zone(zone)')
b = source.index('\t\tavailable = 0;', a) + len('\t\tavailable = 0;')
calculation = source[a:b]
cases = [(0, 0, 0, 0), (0, 100, 0, 0), (10, 50, 100, 0),
         (100, 20, 200, 40), (100, 20, 0, 0), (1, 1000, 1, 1)]
rng = random.Random(8909)
cases += [tuple(rng.randrange(0, 240000) for _ in range(4)) for _ in range(10000)]
rows = []
for free, low, cache, slab in cases:
    expected = max(0, free - low + cache - min(cache // 2, low)
                   + slab - min(slab // 2, low))
    rows.append('{%d,%d,%d,%d,%d}' % (free, low, cache, slab, expected))
harness = '''
#define LRU_ACTIVE_FILE 0
#define LRU_INACTIVE_FILE 1
#define WMARK_LOW 0
#define NR_SLAB_RECLAIMABLE 0
#define min(a,b) ((a)<(b)?(a):(b))
static unsigned long slab_pages;
#define global_page_state(x) slab_pages
struct zone { unsigned long watermark[1]; } z;
#define for_each_zone(zone) for (zone = &z; zone; zone = 0)
static unsigned long calculate(unsigned long free_pages, unsigned long low,
                                unsigned long cache, unsigned long slab) {
    struct { unsigned long freeram; } i = {free_pages};
    unsigned long pages[2] = {cache, 0}, wmark_low = 0, pagecache;
    struct zone *zone;
    long available;
    z.watermark[0] = low; slab_pages = slab;
''' + calculation + '''
    return available;
}
static const unsigned long cases[][5] = {
''' + ',\n'.join(rows) + '''
};
void _start(void) {
    unsigned int n; int rc = 0;
    for (n = 0; n < sizeof(cases)/sizeof(cases[0]); ++n)
        if (calculate(cases[n][0], cases[n][1], cases[n][2], cases[n][3]) != cases[n][4]) { rc = 1; break; }
    register long r0 __asm__("r0") = rc;
    register long r7 __asm__("r7") = 1;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r7) : "memory");
    for (;;) {}
}
'''
(test / 'memavailable.c').write_text(harness)
cross = '/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-'
binary = test / 'memavailable-arm-test'
subprocess.run([cross + 'gcc', '-O2', '-nostdlib', '-static', '-marm', '-march=armv7-a',
                '-fno-stack-protector', '-Wl,-e,_start', str(test / 'memavailable.c'),
                '-o', str(binary)], check=True)
qemu = work / 'host-tools/qemu/usr/bin/qemu-arm'
subprocess.run([str(qemu), '-cpu', 'cortex-a7', str(binary)], check=True, timeout=60)
calls = (kernel / 'arch/arm/kernel/calls.S').read_text().split('#ifndef syscalls_counted')[0]
entries = re.findall(r'CALL\(([^\n]+)\)', calls)
assert len(entries) == 385 and entries[384] == 'sys_getrandom', (len(entries), entries[-6:])
assert entries[382:384] == ['sys_ni_syscall', 'sys_ni_syscall']
assert '#define __NR_syscalls  (388)' in (kernel / 'arch/arm/include/asm/unistd.h').read_text()
assert re.search(r'#define __NR_getrandom\s+\(__NR_SYSCALL_BASE\+384\)',
                 (kernel / 'arch/arm/include/uapi/asm/unistd.h').read_text())
random_source = (kernel / 'drivers/char/random.c').read_text()
assert 'wait_event_interruptible(urandom_init_wait' in random_source
assert 'wake_up_interruptible(&urandom_init_wait)' in random_source
assert 'if (large_request && need_resched())' in random_source
report = {'MemAvailable_ARM32_cases': len(cases), 'getrandom_ARM_EABI_number': 384,
          'padded_syscall_table_entries': 388, 'physical_phone_access': False,
          'limits': ['MemAvailable test uses actual calculation with modeled page counters.',
                     'getrandom checks ABI wiring and source guards, not entropy/runtime behavior.']}
(root / 'interface-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
