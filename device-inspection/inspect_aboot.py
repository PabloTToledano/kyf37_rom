"""Read-only bootloader ELF layout and string reference inventory."""
import json, struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

base = Path(__file__).resolve().parent
source = base.parent / 'phone-backup/kyf37-root-backup/aboot.img'
data = source.read_bytes()
with source.open('rb') as f:
    elf = ELFFile(f)
    segments = [{'offset': s['p_offset'], 'address': s['p_vaddr'],
                 'bytes': s['p_filesz'], 'flags': s['p_flags']}
                for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
    entry = elf['e_entry']
def address(offset):
    for s in segments:
        if s['offset'] <= offset < s['offset'] + s['bytes']:
            return s['address'] + offset - s['offset']
    return None
needles = [b'ANDROID-BOOT!', b'Device is unlocked!', b'oem unlock is not allowed',
           b'fastboot oem unlock-go', b'use_signed_kernel=', b'Need wipe userdata.',
           b'boot_verifier', b'recovery', b'devinfo']
report = {'entry':hex(entry), 'segments':segments, 'strings':[]}
materialized = {}
# Compiler may materialize pointers using MOVW/MOVT rather than literal pools.
for mode in (CS_MODE_ARM, CS_MODE_THUMB):
    decoder = Cs(CS_ARCH_ARM, mode)
    decoder.skipdata = True
    low = {}
    for s in segments:
        for ins in decoder.disasm(data[s['offset']:s['offset']+s['bytes']], s['address']):
            parts = ins.op_str.split(', ')
            if ins.mnemonic.startswith('movw') and len(parts) == 2 and parts[1].startswith('#'):
                low[parts[0]] = (int(parts[1][1:], 0), ins.address)
            elif ins.mnemonic.startswith('movt') and len(parts) == 2 and parts[0] in low:
                value, origin = low[parts[0]]
                if ins.address-origin <= 32:
                    value |= int(parts[1][1:], 0) << 16
                    materialized.setdefault(value, []).append({'instruction':hex(origin), 'mode': 'thumb' if mode == CS_MODE_THUMB else 'arm'})
for needle in needles:
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0: break
        va = address(offset)
        refs = []
        if va is not None:
            literal = struct.pack('<I', va)
            p = 0
            while True:
                p = data.find(literal, p)
                if p < 0: break
                refs.append({'offset':hex(p), 'address':hex(address(p) or 0)})
                p += 1
        report['strings'].append({'text':data[offset:offset+180].split(b'\0')[0].decode(errors='replace'),
                                  'offset':hex(offset), 'address':hex(va) if va is not None else None,
                                  'literal_references':refs, 'movw_movt_references':materialized.get(va, [])})
        start = offset + len(needle)
(base / 'aboot-inventory.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

