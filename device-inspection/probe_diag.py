"""KYF37 diagnostic commands; defaults to read-only root/model checks.

Explicit --factory-flags writes only the verified values 0 or 4 to factory state.
Shell commands execute with diagnostic root privileges; review before use.
"""
import json
import struct
import time
import sys
import usb.core
import usb.util
import libusb_package

def crc(data):
    value = 0xffff
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0x8408 if value & 1 else 0)
    return value ^ 0xffff

def encode(data):
    data += struct.pack('<H', crc(data))
    framed = bytearray()
    for byte in data:
        framed.extend((0x7d, byte ^ 0x20) if byte in (0x7d, 0x7e) else (byte,))
    return bytes(framed) + b'\x7e'

def decode(data):
    decoded = bytearray()
    escaped = False
    for byte in data:
        if escaped:
            decoded.append(byte ^ 0x20)
            escaped = False
        elif byte == 0x7d:
            escaped = True
        else:
            decoded.append(byte)
    if len(decoded) < 2 or crc(decoded[:-2]) != struct.unpack('<H', decoded[-2:])[0]:
        return None
    return bytes(decoded[:-2])

native = '--native' in sys.argv
if native:
    sys.argv.remove('--native')
    from native_winusb import DiagnosticUSB
    device = DiagnosticUSB()
else:
    backend = libusb_package.get_libusb1_backend()
    device = usb.core.find(idVendor=0x05c6, idProduct=0x9091, backend=backend)
if device is None:
    raise SystemExit('KYF37 diagnostic USB device 05c6:9091 not found')
# Interface 0 has bulk OUT 0x01 and bulk IN 0x81, verified from descriptors.
if not native:
    usb.util.claim_interface(device, 0)
header = b'\x4b\xfc\x81\x20'
factory_status = len(sys.argv) > 1 and sys.argv[1] == '--factory-status'
factory_write = len(sys.argv) > 1 and sys.argv[1] == '--factory-flags'
factory_value = None
if factory_write:
    factory_value = int(sys.argv[2])
    if factory_value not in (0, 4):
        raise SystemExit('Only recorded original flags 0 and verified permissive flag 4 allowed')
    header = b'\x4b\xfc\xc0\x20'
if factory_status:
    header = b'\x4b\xfc\xc1\x20'
command = (sys.argv[1] if len(sys.argv) > 1 else 'id; getprop ro.product.model; getprop ro.build.display.id; getenforce').encode()
if len(command) > 1023:
    raise SystemExit('Diagnostic command exceeds verified protocol limit')
try:
    request = header if factory_status else (header + struct.pack('<I', factory_value) if factory_write else header + command + b'\0')
    device.write(0x01, encode(request), timeout=2000)
    pending = bytearray()
    chunks = []
    deadline = time.monotonic() + 10
    complete = False
    while time.monotonic() < deadline and not complete:
        try:
            pending.extend(device.read(0x81, 16384, timeout=500))
        except usb.core.USBTimeoutError:
            continue
        while 0x7e in pending:
            end = pending.index(0x7e)
            packet = decode(pending[:end])
            del pending[:end + 1]
            if packet is None or not packet.startswith(header):
                continue
            if factory_status or factory_write:
                chunks.append(packet.hex())
                complete = True
                break
            if len(packet) >= 9:
                chunks.append(packet[9:].rstrip(b'\0').decode('utf-8', errors='replace'))
                complete = bool(packet[8])
    print(json.dumps({'complete': complete, 'output': ''.join(chunks)}, indent=2))
finally:
    if native:
        device.close()
    else:
        usb.util.release_interface(device, 0)
        usb.util.dispose_resources(device)
