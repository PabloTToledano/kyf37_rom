#ifndef KYF37_IR_UAPI_H
#define KYF37_IR_UAPI_H
#include <linux/types.h>
#include <linux/ioctl.h>
#define KYF37_IR_MAX 1024
/* Durations in microseconds: mark, space, mark ...; flags bit 0 inverts TX,
 * bit 1 selects a 2us optical pulse instead of 1/3 duty. No implicit repeats. */
struct kyf37_ir_request {
 __u32 frequency, count, flags;
 __u32 duration[KYF37_IR_MAX];
};
#define KYF37_IR_SEND _IOW('K', 0x37, struct kyf37_ir_request)
#define KYF37_IR_PROBE _IO('K', 0x38)
#endif
