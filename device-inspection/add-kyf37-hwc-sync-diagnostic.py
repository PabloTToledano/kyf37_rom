from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
for f in ['vendor/kyocera/kyf37/kyf37-vendor.mk','device/kyocera/kyf37/device.mk']:
 for l in (r/f).read_text().splitlines():
  if any(t in l for t in ['hwcomposer','gralloc','liboverlay']):print(f,l)
p=r/'hardware/qcom-caf/msm8916/display/libhwcomposer/hwc_utils.cpp';s=p.read_text()
anchor='''    data.acq_fen_fd_cnt = count;
    fbFd = ctx->dpyAttr[dpy].fd;'''
replacement='''    data.acq_fen_fd_cnt = count;
    // Optional KYF37 diagnostic: complete GPU acquire fences before MDP scanout submission.
    // Preserve real release/retire fences; never substitute or discard them.
    char kyf37Device[PROPERTY_VALUE_MAX] = {0};
    char kyf37Wait[PROPERTY_VALUE_MAX] = {0};
    property_get("ro.product.device", kyf37Device, "");
    property_get("debug.hwc.kyf37_sync_wait", kyf37Wait, "0");
    if (!strcmp(kyf37Device, "kyf37") && !strcmp(kyf37Wait, "1")) {
        data.flags |= MDP_BUF_SYNC_FLAG_WAIT;
    }
    fbFd = ctx->dpyAttr[dpy].fd;'''
if 'debug.hwc.kyf37_sync_wait' not in s:
 assert s.count(anchor)==1;s=s.replace(anchor,replacement);p.write_text(s)
print('Added opt-in acquire-fence wait diagnostic; default behavior unchanged until tested')
