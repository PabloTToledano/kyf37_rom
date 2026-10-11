"""Exercise the native mask parser against saved modem responses without USB."""
from pathlib import Path
import subprocess, tempfile, json
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
source=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/radio-tools/kyf37_qmux.c')
original=json.loads((root/'device-inspection/lte-qmi-original.json').read_text())
readback=(root/'device-inspection/lte-after-reboot.txt').read_text().split('NAS_reply hex=')[1].split()[0]
def array(data): return ','.join(str(b) for b in data)
old=bytes.fromhex(original['response_hex']); new=bytes.fromhex(readback)
error=bytearray(new); error[10]=1; error[12]=1
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    harness='''#define main device_main
#include "%s"
#undef main
#include <assert.h>
int main(void) {
 unsigned char old[]={%s}, updated[]={%s}, failed[]={%s};
 assert(getmask(old,sizeof(old))==0x02000001ULL);
 assert(getmask(updated,sizeof(updated))==0x0a0800c5ULL);
 assert(getmask(failed,sizeof(failed))==0);
 assert(getmask(updated,12)==0);
 return 0;
}
''' % (source,array(old),array(new),array(error))
    (tmp/'test.c').write_text(harness)
    subprocess.run(['gcc','-std=gnu11',str(tmp/'test.c'),'-o',str(tmp/'test')],check=True)
    subprocess.run([str(tmp/'test')],check=True)
mask=int.from_bytes(new[new.index(bytes([0x15,8,0]))+3:][:8],'little')
assert [i+1 for i in range(64) if mask & (1<<i)]==[1,3,7,8,20,26,28]
report={'original_mask':'0x02000001','saved_post_reboot_mask':hex(mask),
        'native_parser_saved_response_tests_passed':True,
        'error_and_truncated_response_rejected':True,
        'phone_accessed':False,'current_modem_state_verified':False}
(root/'kyf37-rom/android10-spain-qmi-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
