"""Apply between builds: restore C ABI used by stock Qualcomm FileMux."""
from pathlib import Path
p=Path('/home/pablo/kyf37-lineage/system/core/libutils/Threads.cpp')
s=p.read_text()
function='''
// Legacy Qualcomm media ABI: return the Linux thread ID, not pthread_t.
#if defined(__ANDROID__)
extern "C" pid_t androidGetTid() {
    return gettid();
}
#endif
'''
if 'pid_t androidGetTid()' not in s:
    assert '#include <unistd.h>' in s
    p.write_text(s+function)
print('Legacy androidGetTid ABI restored using bionic gettid.')
