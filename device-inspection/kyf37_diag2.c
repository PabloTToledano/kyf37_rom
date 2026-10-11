/*
 * kyf37_diag2 - /dev/diag client for the KYF37 (msm-3.10 diag driver), modelled on diag_mdlog.
 *
 * Why the first tool (kyf37_diag.c) saw nothing: diagchar_write(USER_SPACE_DATA_TYPE) feeds the
 * payload to diag_process_hdlc(), which HDLC-decodes it and verifies a CRC-16. Raw (un-framed)
 * commands are silently dropped ("bad CRC"), so no mask ever reached the apps mask tables or the
 * modem (mask centralisation: the apps side pushes masks to the modem over the CNTL channel).
 *
 * This client: opens /dev/diag, switches to MEMORY_DEVICE_MODE, sends HDLC-framed commands
 * (version, ext build id, ssid ranges, set-all msg mask, set per-range msg masks, log masks, event mask),
 * then reads (blocking, in a thread) and decodes the HDLC streams coming from the peripherals.
 *
 * usage: kyf37_diag2 <seconds> [outprefix]    (default /data/local/tmp/diag2)
 * writes <prefix>.raw (every read() verbatim), <prefix>.txt (decoded packets)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <pthread.h>
#include <time.h>
#include <sys/ioctl.h>

#define DIAG_IOCTL_SWITCH_LOGGING 7
#define DIAG_IOCTL_VOTE_REAL_TIME 33
#define DIAG_IOCTL_GET_REAL_TIME 34
#define MEMORY_DEVICE_MODE 2
#define USER_SPACE_DATA_TYPE 0x20
#define MSG_MASKS_TYPE 1
#define LOG_MASKS_TYPE 2
#define EVENT_MASKS_TYPE 4
#define PKT_TYPE 8
#define DEINIT_TYPE 0x10

static FILE *txt, *raw;
static volatile long total_bytes, total_pkts;
static long cmd_hist[256];
static volatile int nranges; static uint16_t rng_first[64], rng_last[64];

static uint16_t crc16(const uint8_t *p, int n) {
  uint16_t c = 0xffff;
  while (n--) { c ^= *p++; for (int i = 0; i < 8; i++) c = (c & 1) ? (c >> 1) ^ 0x8408 : c >> 1; }
  return (uint16_t)~c;
}
static int hdlc_enc(const uint8_t *in, int n, uint8_t *out) {
  uint16_t c = crc16(in, n); int o = 0;
  uint8_t tmp[1024]; memcpy(tmp, in, n); tmp[n] = c & 0xff; tmp[n + 1] = c >> 8;
  for (int i = 0; i < n + 2; i++) {
    if (tmp[i] == 0x7e || tmp[i] == 0x7d) { out[o++] = 0x7d; out[o++] = tmp[i] ^ 0x20; } else out[o++] = tmp[i];
  }
  out[o++] = 0x7e; return o;
}
static int send_cmd(int fd, const uint8_t *pkt, int len, const char *name) {
  uint8_t buf[2200]; int t = USER_SPACE_DATA_TYPE; memcpy(buf, &t, 4);
  int n = hdlc_enc(pkt, len, buf + 4);
  errno = 0; int r = write(fd, buf, n + 4);
  fprintf(txt, "# send %-28s len=%d framed=%d -> %d errno=%d\n", name, len, n, r, r < 0 ? errno : 0); fflush(txt);
  usleep(150000); return r;
}

static void hexdump(const uint8_t *p, int n, int max) {
  for (int i = 0; i < n && i < max; i++) fprintf(txt, "%02x", p[i]);
  if (n > max) fprintf(txt, "...");
}
static void printable(const uint8_t *p, int n) {
  for (int i = 0; i < n; i++) fputc((p[i] >= 0x20 && p[i] < 0x7f) ? p[i] : '.', txt);
}

static void decode_pkt(const uint8_t *p, int n) {
  if (n < 1) return;
  cmd_hist[p[0]]++; total_pkts++;
  if (p[0] == 0x7d && p[1] == 0x01 && n >= 8 && p[2] == 1) { /* get ssid ranges response: 7d 01 status pad count(u32) {first,last}* */
    int c = p[4]; if (c > 64) c = 64; if (8 + 4 * c > n) c = (n - 8) / 4;
    for (int i = 0; i < c; i++) { rng_first[i] = p[8+4*i] | p[9+4*i] << 8; rng_last[i] = p[10+4*i] | p[11+4*i] << 8; }
    nranges = c; }
  if (p[0] == 0x1f && n >= 20) { /* extended msg: 1f ts_type nargs drop ts[8] line ssid mask args fmt file */
    unsigned nargs = p[2]; uint16_t line = p[12] | p[13] << 8, ssid = p[14] | p[15] << 8;
    uint32_t mask = p[16] | p[17] << 8 | p[18] << 16 | (uint32_t)p[19] << 24;
    int off = 20 + 4 * nargs;
    fprintf(txt, "F3 ssid=%u mask=0x%x line=%u args=", ssid, mask, line);
    for (unsigned i = 0; i < nargs && 20 + 4 * i + 4 <= (unsigned)n; i++)
      fprintf(txt, "%u%s", p[20 + 4*i] | p[21+4*i] << 8 | p[22+4*i] << 16 | (uint32_t)p[23+4*i] << 24, i + 1 < nargs ? "," : "");
    if (off < n) { fprintf(txt, " | "); const uint8_t *s = p + off; int l = strnlen((const char *)s, n - off); printable(s, l);
      if (off + l + 1 < n) { fprintf(txt, " | file="); printable(s + l + 1, n - off - l - 1); } }
    fputc('\n', txt);
  } else if (p[0] == 0x79) { fprintf(txt, "QSR79 "); hexdump(p, n, 600); fputc('\n', txt); }
  else if (p[0] == 0x92 || p[0] == 0x98 || p[0] == 0x99) { fprintf(txt, "QSR%02x ", p[0]); hexdump(p, n, 600); fputc('\n', txt); }
  else if (p[0] == 0x10) { fprintf(txt, "LOG len=%d code=0x%04x\n", n, n >= 12 ? p[10] | p[11] << 8 : 0); }
  else if (p[0] == 0x60) { fprintf(txt, "EVENT-RPT len=%d\n", n); }
  else { fprintf(txt, "PKT %02x len=%d ", p[0], n); hexdump(p, n, 48); fputs(" |", txt); printable(p, n > 80 ? 80 : n); fputc('\n', txt); }
}

/* streaming HDLC decoder across reads */
static uint8_t acc[65536]; static int acclen, esc;
static void feed(const uint8_t *p, int n) {
  for (int i = 0; i < n; i++) {
    uint8_t b = p[i];
    if (b == 0x7e) { if (acclen >= 3) { if (crc16(acc, acclen - 2) == (uint16_t)(acc[acclen-2] | acc[acclen-1] << 8)) decode_pkt(acc, acclen - 2); else { fprintf(txt, "BADCRC len=%d ", acclen); hexdump(acc, acclen, 32); fputc('\n', txt);} } acclen = 0; esc = 0; continue; }
    if (esc) { b ^= 0x20; esc = 0; } else if (b == 0x7d) { esc = 1; continue; }
    if (acclen < (int)sizeof acc) acc[acclen++] = b;
  }
}

static void *reader(void *arg) {
  int fd = *(int *)arg; static uint8_t buf[262144];
  for (;;) {
    int n = read(fd, buf, sizeof buf);
    if (n <= 0) { if (n < 0 && errno != EINTR && errno != EAGAIN) { fprintf(txt, "# read err %d\n", errno); fflush(txt); } usleep(20000); continue; }
    total_bytes += n; if (raw) { fwrite(buf, 1, n, raw); fflush(raw); }
    int type = *(int *)buf;
    if (type == USER_SPACE_DATA_TYPE && n >= 8) {
      int num = *(int *)(buf + 4), pos = 8;
      fprintf(txt, "# read %d bytes: USER_SPACE_DATA entries=%d\n", n, num);
      for (int e = 0; e < num && pos + 4 <= n; e++) {
        int l = *(int *)(buf + pos); pos += 4; if (l < 0 || pos + l > n) break;
        feed(buf + pos, l); pos += l;
      }
    } else fprintf(txt, "# read %d bytes: type=0x%x (%s)\n", n, type,
        type == MSG_MASKS_TYPE ? "msg mask table" : type == LOG_MASKS_TYPE ? "log mask" : type == EVENT_MASKS_TYPE ? "event mask" : type == PKT_TYPE ? "pkt" : "other");
    fflush(txt);
  }
  fflush(NULL); _exit(0);
}

int main(int argc, char **argv) {
  int secs = argc > 1 ? atoi(argv[1]) : 20; const char *pre = argc > 2 ? argv[2] : "/data/local/tmp/diag2";
  char path[256]; setbuf(stdout, NULL);
  if (!strcmp(pre, "-")) { txt = stdout; raw = fopen("/data/local/tmp/diag2.raw", "wb"); } else { snprintf(path, sizeof path, "%s.txt", pre); txt = fopen(path, "w"); snprintf(path, sizeof path, "%s.raw", pre); raw = fopen(path, "wb"); }
  int unsafe = argc > 3 && strstr(argv[3], "unsafe");
  if (!txt) { perror("txt"); return 1; }
  int fd = open("/dev/diag", O_RDWR); if (fd < 0) { perror("open /dev/diag"); return 1; }
  pthread_t th; pthread_create(&th, 0, reader, &fd);
  int mode = MEMORY_DEVICE_MODE; int r = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &mode);
  fprintf(txt, "# switch_logging ret=%d errno=%d\n", r, r < 0 ? errno : 0);
  struct { int proc; uint8_t vote; } v = { 0, 1 }; r = ioctl(fd, DIAG_IOCTL_VOTE_REAL_TIME, &v);
  fprintf(txt, "# vote_real_time ret=%d errno=%d\n", r, r < 0 ? errno : 0);
  int rt = -1; r = ioctl(fd, DIAG_IOCTL_GET_REAL_TIME, &rt); fprintf(txt, "# get_real_time ret=%d val=%d\n", r, rt);
  fflush(txt); usleep(300000);

  uint8_t c0[] = {0x00}; send_cmd(fd, c0, 1, "version(0x00)");
  uint8_t c1[] = {0x1c}; send_cmd(fd, c1, 1, "diag version(0x1c)");
  uint8_t c2[] = {0x7c}; send_cmd(fd, c2, 1, "ext build id(0x7c)");
  uint8_t c3[] = {0x1d}; send_cmd(fd, c3, 1, "timestamp(0x1d)");
  uint8_t c4[] = {0x7d, 0x01, 0, 0, 0, 0, 0, 0}; send_cmd(fd, c4, 8, "msg get ssid ranges");
  /* DO NOT send 0x7d/0x05 (set-all) with a non-zero mask: in this kernel diag_send_msg_mask_update() never resets
   * mask_size inside its loop for the ALL_ENABLED case, so the control packet grows x4 per range and overflows the
   * 4 KB update buffer (heap corruption -> panic in an unrelated driver, reproduced twice on 2026-10-10). Only with "allmask": */
  if (argc > 3 && strstr(argv[3], "allmask")) { uint8_t c5[] = {0x7d, 0x05, 0, 0, 0xff, 0xff, 0xff, 0xff}; send_cmd(fd, c5, 8, "msg SET ALL mask (BUGGY)"); }
  /* Safe path: set every range EXACTLY as the driver reports it (no krealloc, update packet <= 811 bytes). */
  for (int w = 0; w < 30 && !nranges; w++) usleep(100000);
  fprintf(txt, "# ssid ranges known: %d\n", nranges);
  for (int i = 0; i < nranges; i++) {
    uint8_t pk[8 + 4 * 256]; uint16_t a = rng_first[i], b = rng_last[i]; int cnt = b - a + 1; if (cnt < 1 || cnt > 200) continue;
    pk[0] = 0x7d; pk[1] = 0x04; pk[2] = a; pk[3] = a >> 8; pk[4] = b; pk[5] = b >> 8; pk[6] = 0; pk[7] = 0;
    memset(pk + 8, 0xff, 4 * cnt); char nm[48]; snprintf(nm, sizeof nm, "msg set range %u-%u (exact)", a, b);
    send_cmd(fd, pk, 8 + 4 * cnt, nm);
  }
  /* KERNEL BUG WARNING (verified 2026-10-10: panic on KYF37 kernel #17): diag_send_msg_mask_update() and
   * diag_send_event_mask_update() krealloc() their update buffer but keep writing through the stale local
   * pointer (use-after-free) whenever msg_mask.status==VALID (per-range set 0x7d/0x04, event set 0x82, log set 0x73).
   * That corrupted the heap and panicked the phone. Those commands are only sent with the "unsafe" argument. */
  { uint8_t pk[] = {0x60, 0x01}; send_cmd(fd, pk, 2, "event toggle ALL on (safe)"); }
  if (unsafe) {
  /* explicit per-range set (0x7d 0x04): first,last,status,pad, then (last-first+1) u32 masks */
  static const struct { uint16_t a, b; } ranges[] = {{0,0x1f4},{500,0x1f4+0},{1000,1080},{2000,2100},{3000,3100},{4000,4100},{4500,4600},{5000,5100},{5500,5600},{6000,6100},{7000,7100},{8000,8100},{9000,9100}};
  for (unsigned i = 0; i < sizeof ranges / sizeof ranges[0]; i++) {
    uint8_t pk[8 + 4 * 128]; uint16_t a = ranges[i].a, b = ranges[i].b; if (b < a) b = a; if (b - a > 127) b = a + 127;
    pk[0] = 0x7d; pk[1] = 0x04; pk[2] = a; pk[3] = a >> 8; pk[4] = b; pk[5] = b >> 8; pk[6] = 0; pk[7] = 0;
    memset(pk + 8, 0xff, 4 * (b - a + 1)); char nm[40]; snprintf(nm, sizeof nm, "msg set range %u-%u", a, b);
    send_cmd(fd, pk, 8 + 4 * (b - a + 1), nm);
  }
  /* event mask: 0x82 status pad num_bits(u16) + mask, then enable events 0x60 0x01 */
  { uint8_t pk[5 + 501]; pk[0] = 0x82; pk[1] = 0; pk[2] = 0; pk[3] = 4000 & 0xff; pk[4] = 4000 >> 8; memset(pk + 5, 0xff, 501); send_cmd(fd, pk, 506, "event set mask"); }
  /* log masks: 0x73 00 00 00 | sub=3 | equip | num_items | mask */
  for (uint32_t eq = 0; eq < 16; eq++) {
    uint8_t pk[16 + 64] = {0x73}; uint32_t sub = 3, ni = 512;
    memcpy(pk + 4, &sub, 4); memcpy(pk + 8, &eq, 4); memcpy(pk + 12, &ni, 4); memset(pk + 16, 0xff, 64);
    char nm[40]; snprintf(nm, sizeof nm, "log set equip %u", eq); send_cmd(fd, pk, 80, nm);
  }
  }
  /* re-query version after masks to prove the command channel */
  send_cmd(fd, c2, 1, "ext build id again");

  time_t end = time(0) + secs;
  while (time(0) < end) { sleep(1); }
  fprintf(txt, "# done total_bytes=%ld packets=%ld\n# cmd histogram:", total_bytes, total_pkts);
  for (int i = 0; i < 256; i++) if (cmd_hist[i]) fprintf(txt, " 0x%02x:%ld", i, cmd_hist[i]);
  fputc('\n', txt); fflush(txt);
  printf("done total_bytes=%ld packets=%ld\n", total_bytes, total_pkts);
  /* restore USB mode (the stock default) so we leave the driver as we found it */
  mode = 1; ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &mode);
  fflush(NULL); _exit(0);
}
