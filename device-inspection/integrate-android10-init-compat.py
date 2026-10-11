from pathlib import Path
import subprocess, struct, json

tree = Path('/home/pablo/kyf37-android10')
if subprocess.run(['pgrep', '-x', 'ninja'], stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Stop the build before editing inputs')
stock = Path('/home/pablo/kyf37-rom/stock-system/lib/libc.so').read_bytes()
evidence = {}
for name, expected in [('qcom_diag',3009), ('net_bt_stack',3008)]:
    offset = stock.index(name.encode()+b'\0')
    # In this stock ELF, the read-only PT_LOAD has equal file and virtual offsets.
    phoff = struct.unpack_from('<I', stock, 28)[0]
    phsize, phnum = struct.unpack_from('<HH', stock,42)
    address = None
    for i in range(phnum):
        typ, off, va, _, size = struct.unpack_from('<IIIII',stock,phoff+i*phsize)
        if typ == 1 and off <= offset < off+size:
            address = va + offset-off
    assert address is not None
    needle = struct.pack('<I', address)
    matches = []
    for pos in range(0,len(stock)-8,4):
        if stock[pos:pos+4] == needle and struct.unpack_from('<I',stock,pos+4)[0] == expected:
            matches.append(pos)
    assert matches, (name,expected)
    evidence[name] = {'id':expected,'name_virtual_address':address,'table_offsets':matches}
ramdisk = tree/'device/kyocera/kyf37/ramdisk'
for path in ramdisk.glob('*.rc'):
    content = path.read_text()
    content = content.replace('qcom_diag','3009').replace('net_bt_stack','3008')
    content = content.replace('user radio system','user radio')
    content = '\n'.join('# Android 10 loads system properties during second-stage init.' if line.strip() == 'load_all_props' else line for line in content.splitlines())+'\n'
    path.write_text(content)
report = {'stock_libc_account_evidence':evidence,'verification':{}}
verifier = tree/'out/host/linux-x86/bin/host_init_verifier'
passwd = tree/'out/target/product/kyf37/obj/ETC/passwd_intermediates/passwd'
for path in sorted(ramdisk.glob('init*.rc')):
    result = subprocess.run([str(verifier),str(path),str(passwd)],capture_output=True,text=True)
    report['verification'][path.name] = {'exit_code':result.returncode,'output':result.stdout+result.stderr}
dest = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/android10-init-compat.json')
dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert all(v['exit_code']==0 for v in report['verification'].values())
