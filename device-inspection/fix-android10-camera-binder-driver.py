from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'hardware/interfaces/camera/provider/2.4/default/service.cpp'
s=p.read_text()
if 'KYF37 legacy HAL checks' not in s:
 s=s.replace('#include <binder/ProcessState.h>', '#include <binder/ProcessState.h>\n#include <sys/system_properties.h>\n#include <cstring>')
 s=s.replace('android::ProcessState::initWithDriver("/dev/vndbinder");','''// KYF37 legacy HAL checks OEM camera permission through framework permission service.
    char device[PROP_VALUE_MAX] = {};
    __system_property_get("ro.product.device", device);
    android::ProcessState::initWithDriver(
            std::strcmp(device, "kyf37") == 0 ? "/dev/binder" : "/dev/vndbinder");''')
 p.write_text(s)
print('KYF37 provider routes old HAL permission checks to actual framework Binder')
