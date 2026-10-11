"""Use supported synchronous ADB and the KYF37's original Qualcomm BT NV record."""
from pathlib import Path

tree = Path('/home/pablo/kyf37-android10')
device = tree / 'device/kyocera/kyf37'
make = device / 'device.mk'
props = ('\n# Linux 3.10 FunctionFS has no asynchronous endpoint I/O.\n'
         'PRODUCT_PROPERTY_OVERRIDES += ro.adb.nonblocking_ffs=false sys.usb.ffs.aio_compat=true\n'
         '# Read the factory address from its existing, unmodified Qualcomm NV record.\n'
         'PRODUCT_PROPERTY_OVERRIDES += ro.bt.bdaddr_path=/persist/.bt_nv.bin\n')
content = make.read_text()
if 'ro.adb.nonblocking_ffs=false' not in content:
    make.write_text(content + props)

address = tree / 'hardware/interfaces/bluetooth/1.0/default/bluetooth_address.cc'
source = address.read_text()
anchor = '    if (addr_fd != -1) {\n'
addition = '''      // KYF37 stores a Qualcomm NV item: id, protection, length, six address bytes.
      // Scope binary decoding to the explicitly configured OEM path; other devices
      // retain the standard text parser. Never alter the factory NV file.
      if (!strcmp(property, "/persist/.bt_nv.bin")) {
        uint8_t record[10] = {0};
        ssize_t size = read(addr_fd, record, sizeof(record));
        if (size == 9 && record[0] == 1 && record[1] <= 1 && record[2] == kBytes) {
          const uint8_t zero[kBytes] = {0};
          const uint8_t invalid[kBytes] = {255, 255, 255, 255, 255, 255};
          if (memcmp(record + 3, zero, kBytes) && memcmp(record + 3, invalid, kBytes)) {
            memcpy(local_addr, record + 3, kBytes);
            close(addr_fd);
            return true;
          }
        }
        lseek(addr_fd, 0, SEEK_SET);
      }
'''
if 'KYF37 stores a Qualcomm NV item' not in source:
    assert source.count(anchor) == 1
    address.write_text(source.replace(anchor, anchor + addition))
print('Legacy synchronous ADB properties and factory Bluetooth NV reader staged')
