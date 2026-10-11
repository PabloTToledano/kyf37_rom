"""Run the actual backported ARM32 LZ4 sources under host QEMU, never ADB."""
from pathlib import Path
import json
import shutil
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
test = work / 'host-tests/lz4'
test.mkdir(parents=True, exist_ok=True)
inc = test / 'include'
(inc / 'linux').mkdir(parents=True, exist_ok=True)
(inc / 'asm').mkdir(parents=True, exist_ok=True)
(inc / 'linux/module.h').write_text('#define EXPORT_SYMBOL(x)\n#define MODULE_LICENSE(x)\n#define MODULE_DESCRIPTION(x)\n')
(inc / 'linux/kernel.h').write_text('''#ifndef TEST_KERNEL_H
#define TEST_KERNEL_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef unsigned int size_t;
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
void *memcpy(void *, const void *, size_t);
void *memset(void *, int, size_t);
#endif
''')
(inc / 'asm/unaligned.h').write_text('''#include <linux/kernel.h>
#define get_unaligned(p) ({ __typeof__(*(p)) value; memcpy((void *)&value, (p), sizeof(value)); value; })
#define put_unaligned(v,p) do { __typeof__(*(p)) value = (v); memcpy((p), &value, sizeof(value)); } while (0)
#define get_unaligned_le16(p) get_unaligned((const u16 *)(p))
#define put_unaligned_le16(v,p) put_unaligned((v),(u16 *)(p))
''')
shutil.copyfile(work / 'kernel/include/linux/lz4.h', inc / 'linux/lz4.h')
harness = r'''
#include <linux/kernel.h>
#include <linux/lz4.h>
static unsigned char source[4096 + 32], compressed[8192 + 32], decoded[4096 + 32];
static unsigned long wrkmem[4096];
void *memcpy(void *d, const void *s, size_t n) {
    unsigned char *a = d; const unsigned char *b = s;
    while (n--) *a++ = *b++;
    return d;
}
void *memset(void *d, int c, size_t n) {
    unsigned char *p = d; while (n--) *p++ = c; return d;
}
static int same(const unsigned char *a, const unsigned char *b, size_t n) {
    while (n--) if (*a++ != *b++) return 0; return 1;
}
static int run(void) {
    unsigned int seed = 0x12345678, trial, i;
    for (trial = 0; trial < 10000; ++trial) {
        size_t n = 4096, clen = 8192, dlen = 4096;
        unsigned char *src = source + (trial & 3), *cmp = compressed + (trial & 3);
        unsigned char *out = decoded + (trial & 3);
        for (i = 0; i < n; ++i) {
            seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
            src[i] = trial % 4 == 0 ? 0 : trial % 4 == 1 ? i % 19 :
                     trial % 4 == 2 ? (i / 64) % 31 : seed;
        }
        memset(out, 0xa5, n + 16);
        if (lz4_compress(src, n, cmp, &clen, wrkmem)) return 10;
        if (clen > lz4_compressbound(n)) return 11;
        if (lz4_decompress_unknownoutputsize(cmp, clen, out, &dlen)) return 12;
        if (dlen != n || !same(src, out, n)) return 13;
        for (i = n; i < n + 16; ++i) if (out[i] != 0xa5) return 14;
        /* The safe decoder must reject an undersized output buffer. */
        dlen = n - 1;
        if (!lz4_decompress_unknownoutputsize(cmp, clen, out, &dlen)) return 15;
        /* Removing the final byte must not decode a full page successfully. */
        dlen = n;
        if (!lz4_decompress_unknownoutputsize(cmp, clen - 1, out, &dlen) && dlen == n) return 16;
    }
    return 0;
}
void _start(void) {
    int rc = run();
    register long r0 __asm__("r0") = rc;
    register long r7 __asm__("r7") = 1;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r7) : "memory");
    for (;;) {}
}
'''
(test / 'harness.c').write_text(harness)
cross = '/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-gcc'
sources = work / 'kernel/lib/lz4'
binary = test / 'lz4-arm-test'
subprocess.run([cross, '-O2', '-fno-builtin', '-fno-strict-aliasing', '-fno-stack-protector',
                '-nostdlib', '-static', '-marm', '-march=armv7-a', '-mfloat-abi=soft',
                '-I' + str(inc), '-Wl,-e,_start', str(test / 'harness.c'),
                str(sources / 'lz4_compress.c'), str(sources / 'lz4_decompress.c'),
                '-lgcc', '-o', str(binary)], check=True)
tools = work / 'host-tools'
packages = list(tools.glob('qemu-user_*.deb'))
assert len(packages) == 1, packages
unpacked = tools / 'qemu'
subprocess.run(['dpkg-deb', '-x', str(packages[0]), str(unpacked)], check=True)
qemu = unpacked / 'usr/bin/qemu-arm'
result = subprocess.run([str(qemu), '-cpu', 'cortex-a7', str(binary)], timeout=120)
report = {'actual_source': str(sources), 'architecture': 'ARM32, Cortex-A7 user-mode emulation',
          'trials': 10000, 'tests': ['page round trips: zero/repetitive/structured/random',
                     'unaligned buffers', 'output canaries', 'undersized output rejection',
                     'truncated compressed page rejection'], 'exit_code': result.returncode,
          'physical_phone_access': False,
          'limit': 'Tests codec code, not kernel zram locking or device performance.'}
(root / 'arm-lz4-test.json').write_text(json.dumps(report, indent=2) + '\n')
assert result.returncode == 0, report
print(json.dumps(report, indent=2))
