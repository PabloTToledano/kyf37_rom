from pathlib import Path
import subprocess
tree=Path('/home/pablo/kyf37-android10')
if subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Build active')
def replace(rel,old,new):
    p=tree/rel;s=p.read_text()
    if new in s:return
    assert old in s,rel
    p.write_text(s.replace(old,new,1))
replace('external/boringssl/sources.bp','    name: "libcrypto_sources",\n    srcs: [','    name: "libcrypto_sources",\n    srcs: [\n        "src/decrepit/bio/base64_bio.c",')
# Export the real header implementations with their original atomic semantics.
(tree/'system/core/libcutils/kyf37_legacy_atomics.c').write_text('#define ANDROID_ATOMIC_INLINE\n#include <cutils/atomic.h>\n')
replace('system/core/libcutils/Android.bp','        "config_utils.cpp",','        "kyf37_legacy_atomics.c",\n        "config_utils.cpp",')
replace('frameworks/native/libs/binder/include/binder/IInterface.h','            IInterface();','            IInterface();\n            sp<IBinder> asBinder(); // Legacy instance entry point, no vtable change.')
replace('frameworks/native/libs/binder/IInterface.cpp','// static\nsp<IBinder> IInterface::asBinder(const IInterface* iface)','sp<IBinder> IInterface::asBinder() { return onAsBinder(); }\n\n// static\nsp<IBinder> IInterface::asBinder(const IInterface* iface)')
replace('frameworks/native/libs/binder/include/binder/MemoryHeapBase.h','    // init() takes ownership of fd','    status_t init(int fd, void *base, int size, int flags, const char* device);\n    // init() takes ownership of fd')
replace('frameworks/native/libs/binder/MemoryHeapBase.cpp','status_t MemoryHeapBase::init(int fd, void *base, size_t size, int flags, const char* device)','status_t MemoryHeapBase::init(int fd, void *base, int size, int flags, const char* device)\n{\n    if (size < 0) return BAD_VALUE;\n    return init(fd, base, static_cast<size_t>(size), flags, device);\n}\n\nstatus_t MemoryHeapBase::init(int fd, void *base, size_t size, int flags, const char* device)')
replace('frameworks/native/libs/ui/include/ui/GraphicBuffer.h','    status_t lock(uint32_t inUsage, void** vaddr, int32_t* outBytesPerPixel = nullptr,','    status_t lock(uint32_t inUsage, void** vaddr);\n    status_t lock(uint32_t inUsage, void** vaddr, int32_t* outBytesPerPixel,')
replace('frameworks/native/libs/ui/GraphicBuffer.cpp','status_t GraphicBuffer::lock(uint32_t inUsage, void** vaddr, int32_t* outBytesPerPixel,','status_t GraphicBuffer::lock(uint32_t inUsage, void** vaddr) {\n    return lock(inUsage, vaddr, nullptr, nullptr);\n}\n\nstatus_t GraphicBuffer::lock(uint32_t inUsage, void** vaddr, int32_t* outBytesPerPixel,')
replace('frameworks/native/libs/ui/include/ui/GraphicBufferMapper.h','    status_t lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds, void** vaddr,\n                  int32_t* outBytesPerPixel = nullptr,','    status_t lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds, void** vaddr);\n    status_t lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds, void** vaddr,\n                  int32_t* outBytesPerPixel,')
replace('frameworks/native/libs/ui/GraphicBufferMapper.cpp','status_t GraphicBufferMapper::lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds,','status_t GraphicBufferMapper::lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds, void** vaddr) {\n    return lock(handle, usage, bounds, vaddr, nullptr, nullptr);\n}\n\nstatus_t GraphicBufferMapper::lock(buffer_handle_t handle, uint32_t usage, const Rect& bounds,')
p=tree/'device/kyocera/kyf37/device.mk';s=p.read_text()
line='PRODUCT_PACKAGES += libaudioroute libtinycompress libcnefeatureconfig\n'
if line not in s:p.write_text(s+'\n# Real source providers required by retained stock ELF dependencies.\n'+line)
print('Real base64 BIO, header atomics, forwarding Binder/graphics overloads and required source libraries integrated.')
