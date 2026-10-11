"""Compare imported stock module CRCs with the exact rebuilt kernel exports."""
from pathlib import Path
import struct, json, subprocess, hashlib, argparse
parser = argparse.ArgumentParser()
parser.add_argument('--base', type=Path, default=Path('/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary/lib/modules'))
parser.add_argument('--report', type=Path, default=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/android10-kernel-module-audit.json'))
parser.add_argument('--build-dir', type=Path, default=Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build'))
args = parser.parse_args()
base = args.base
build = args.build_dir
exports = {}
for line in (build/'Module.symvers').read_text().splitlines():
    fields = line.split()
    exports[fields[1]] = int(fields[0], 16)
reports = []
for path in sorted(base.rglob('*.ko')):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x01', path
    offset = struct.unpack_from('<I', data, 32)[0]
    size, count, names_index = struct.unpack_from('<HHH', data, 46)
    sections = [struct.unpack_from('<10I', data, offset+i*size) for i in range(count)]
    names_section = sections[names_index]
    names = data[names_section[4]:names_section[4]+names_section[5]]
    # The OEM ARM module loader has an explicit relocation switch. Ignore
    # debug-section relocations, which are never loaded into kernel memory.
    allowed_relocations = {0, 1, 2, 10, 28, 29, 30, 40, 42, 43, 44, 47, 48}
    loaded_relocations = set()
    unsupported_relocations = []
    for section in sections:
        if section[1] != 9 or not (sections[section[7]][2] & 2):
            continue
        assert section[9] == 8 and section[5] % 8 == 0
        section_name = names[section[0]:].split(b'\0', 1)[0].decode()
        for pos in range(section[4], section[4] + section[5], 8):
            offset, info = struct.unpack_from('<2I', data, pos)
            relocation = info & 0xff
            loaded_relocations.add(relocation)
            if relocation not in allowed_relocations:
                unsupported_relocations.append({'section':section_name, 'offset':offset, 'type':relocation})
    versions = None
    for section in sections:
        name = names[section[0]:].split(b'\0', 1)[0]
        if name == b'__versions':
            versions = data[section[4]:section[4]+section[5]]
    missing, mismatches, checked = [], [], 0
    if versions is not None:
        assert len(versions) % 64 == 0
        for index in range(0, len(versions), 64):
            crc = struct.unpack_from('<I', versions, index)[0]
            symbol = versions[index+4:index+64].split(b'\0', 1)[0].decode()
            checked += 1
            if symbol not in exports:
                missing.append(symbol)
            elif exports[symbol] != crc:
                mismatches.append({'symbol':symbol, 'module_crc':hex(crc), 'kernel_crc':hex(exports[symbol])})
    strings = subprocess.check_output(['strings', str(path)], text=True)
    vermagic = next((s.removeprefix('vermagic=') for s in strings.splitlines() if s.startswith('vermagic=')), None)
    report = {'file':str(path.relative_to(base)), 'sha256':hashlib.sha256(data).hexdigest(),
              'vermagic':vermagic, 'checked_import_crcs':checked, 'missing_exports':missing,
              'crc_mismatches':mismatches, 'has_versions':versions is not None,
              'loaded_relocation_types':sorted(loaded_relocations),
              'unsupported_loaded_relocations':unsupported_relocations}
    reports.append(report)
    print(report['file'], 'checked', checked, 'missing', len(missing), 'CRC mismatches', len(mismatches),
          'unsupported loaded relocations', len(unsupported_relocations))
output = args.report
output.write_text(json.dumps({'kernel_build':str(build), 'modules':reports,
                             'note':'Static CRC/exports and OEM ARM loader relocation checks; not proof of runtime or structure compatibility.'}, indent=2)+'\n')
assert not any(r['missing_exports'] or r['crc_mismatches'] or r['unsupported_loaded_relocations'] for r in reports), 'Module compatibility audit failed; inspect report.'
