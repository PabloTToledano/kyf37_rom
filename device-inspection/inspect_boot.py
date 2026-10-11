import pathlib, struct, zlib
from loguru import logger
from androguard.core.dex import DEX
logger.remove()
root = pathlib.Path(__file__).resolve().parent
data = (root / 'boot.oat').read_bytes()
offset = 0
lines = []
while True:
    offset = data.find(b'dex\n035\0', offset)
    if offset < 0:
        break
    size = struct.unpack_from('<I', data, offset + 32)[0]
    raw = bytearray(data[offset:offset + size])
    offset += 8
    if b'clomask' not in raw:
        continue
    struct.pack_into('<I', raw, 8, zlib.adler32(raw[12:]) & 0xffffffff)
    dex = DEX(bytes(raw))
    for cls in dex.get_classes():
        if 'clomask' not in cls.get_name():
            continue
        print(cls.get_name())
        for method in cls.get_methods():
            lines.append('\n' + cls.get_name() + ' ' + method.get_name() + ' ' + method.get_descriptor())
            lines.extend(i.get_name() + ' ' + i.get_output() for i in method.get_instructions())
(root / 'clomask-disassembly.txt').write_text('\n'.join(lines), encoding='utf-8')
