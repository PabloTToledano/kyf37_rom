import pathlib
import struct
import zlib
import sys
from loguru import logger
from androguard.core.dex import DEX

logger.remove()
root = pathlib.Path(__file__).resolve().parent
for name in (sys.argv[1:2] or ('DiagService.odex', 'services.odex')):
    data = (root / name).read_bytes()
    offset = data.find(b'dex\n035\0')
    if offset < 0:
        raise ValueError(f'No embedded DEX in {name}')
    size = struct.unpack_from('<I', data, offset + 32)[0]
    extracted = bytearray(data[offset:offset + size])
    struct.pack_into('<I', extracted, 8, zlib.adler32(extracted[12:]) & 0xffffffff)
    dex = DEX(bytes(extracted))
    lines = []
    for cls in dex.get_classes():
        if len(sys.argv) > 2 and sys.argv[2].lower() not in cls.get_name().lower():
            continue
        if name == 'services.odex' and not any(s in cls.get_name() for s in ('UsbDeviceManager', 'Transfer', 'Clomask')):
            continue
        for method in cls.get_methods():
            lines.append(f'\n{cls.get_name()} {method.get_name()} {method.get_descriptor()}')
            try:
                for ins in method.get_instructions():
                    lines.append(f'{ins.get_name()} {ins.get_output()}')
            except Exception as error:
                lines.append(f'UNDECODED OPTIMIZED METHOD: {error}')
    (root / (name + '.disassembly.txt')).write_text('\n'.join(lines), encoding='utf-8')
    print(name, 'DEX bytes', size, 'instruction lines', len(lines))
