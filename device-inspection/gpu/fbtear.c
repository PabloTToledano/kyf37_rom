/* fbtear: moving white bar on /dev/graphics/fb0 via FBIOPAN_DISPLAY page flipping (the stock Android 5 scanout path,
 * no SurfaceFlinger/GPU/HWC/ION involved). Run with SurfaceFlinger stopped. Static, no libc (raw ARM EABI syscalls).
 * Tearing => a horizontal break in the bar. Clean here but torn under Android => cause is in the SF/GPU/HWC/ION path. */
#define SYS_exit 1
#define SYS_write 4
#define SYS_open 5
#define SYS_ioctl 54
#define SYS_nanosleep 162
#define SYS_mmap2 192
static long sc(long n, long a, long b, long c, long d, long e, long f) {
  register long r7 __asm__("r7") = n; register long r0 __asm__("r0") = a; register long r1 __asm__("r1") = b;
  register long r2 __asm__("r2") = c; register long r3 __asm__("r3") = d; register long r4 __asm__("r4") = e; register long r5 __asm__("r5") = f;
  __asm__ volatile("svc 0" : "+r"(r0) : "r"(r7), "r"(r1), "r"(r2), "r"(r3), "r"(r4), "r"(r5) : "memory");
  return r0;
}
struct fb_bitfield { unsigned offset, length, msb_right; };
struct fb_var { unsigned xres, yres, xres_virtual, yres_virtual, xoffset, yoffset, bits_per_pixel, grayscale;
  struct fb_bitfield red, green, blue, transp; unsigned rest[16]; };
void _start(void) {
  struct fb_var v; int fd = sc(SYS_open, (long)"/dev/graphics/fb0", 2, 0, 0, 0, 0);
  if (fd < 0 || sc(SYS_ioctl, fd, 0x4600, (long)&v, 0, 0, 0) < 0) sc(SYS_exit, 1, 0, 0, 0, 0, 0);
  unsigned stride = v.xres_virtual; unsigned len = stride * v.yres_virtual * 4;
  unsigned *m = (unsigned *)sc(SYS_mmap2, 0, len, 3, 1, fd, 0);
  unsigned pages = 0; for (unsigned t = v.yres; t <= v.yres_virtual; t += v.yres) pages++; if (pages > 3) pages = 3; if (pages < 2) pages = 2;
  for (unsigned i = 0; i < stride * v.yres_virtual; i++) m[i] = 0;
  int px[3] = {0, 0, 0}; int x = 0, dir = 8; unsigned cur = 0;
  for (int f = 0; f < 1800; f++) {
    unsigned p = cur + 1; if (p >= pages) p = 0; unsigned *pg = m + p * v.yres * stride;
    for (unsigned y = 0; y < v.yres; y++) { unsigned *row = pg + y * stride;
      for (int i = 0; i < 48; i++) { row[px[p] + i] = 0; }
      for (int i = 0; i < 48; i++) { row[x + i] = 0x00ffffff; } }
    px[p] = x; v.yoffset = p * v.yres;
    sc(SYS_ioctl, fd, 0x4606, (long)&v, 0, 0, 0); /* FBIOPAN_DISPLAY, blocks until the frame is latched */
    cur = p; x += dir; if (x > (int)v.xres - 60 || x < 4) dir = -dir;
  }
  sc(SYS_exit, 0, 0, 0, 0, 0, 0);
}
