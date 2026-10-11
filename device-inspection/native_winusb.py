"""Open only the verified diagnostic interface, leaving the ADB interface alone."""
import ctypes as C
from ctypes import wintypes as W
import winreg
import usb.core

class DiagnosticUSB:
    def __init__(self):
        key_name = r'SYSTEM\CurrentControlSet\Enum\USB\VID_05C6&PID_9091&MI_00\8&1C2B3FE0&0&0000\Device Parameters'
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name) as key:
            guids = winreg.QueryValueEx(key, 'DeviceInterfaceGUIDs')[0]
        guid = guids[0] if isinstance(guids, list) else guids
        path = r'\\?\usb#vid_05c6&pid_9091&mi_00#8&1c2b3fe0&0&0000#' + guid
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.api = C.WinDLL('winusb', use_last_error=True)
        self.kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
        self.kernel.CreateFileW.restype = W.HANDLE
        self.kernel.CloseHandle.argtypes = [W.HANDLE]
        self.api.WinUsb_Initialize.argtypes = [W.HANDLE, C.POINTER(W.HANDLE)]
        self.api.WinUsb_Initialize.restype = W.BOOL
        self.api.WinUsb_Free.argtypes = [W.HANDLE]
        self.api.WinUsb_SetPipePolicy.argtypes = [W.HANDLE, C.c_ubyte, W.ULONG, W.ULONG, C.c_void_p]
        for name in ('WinUsb_ReadPipe', 'WinUsb_WritePipe'):
            fn = getattr(self.api, name)
            fn.argtypes = [W.HANDLE, C.c_ubyte, C.c_void_p, W.ULONG, C.POINTER(W.ULONG), C.c_void_p]
            fn.restype = W.BOOL
        self.file = self.kernel.CreateFileW(path, 0xc0000000, 3, None, 3, 0x40000000, None)
        if self.file == C.c_void_p(-1).value:
            raise C.WinError(C.get_last_error())
        self.handle = W.HANDLE()
        if not self.api.WinUsb_Initialize(self.file, C.byref(self.handle)):
            self.kernel.CloseHandle(self.file)
            raise C.WinError(C.get_last_error())

    def transfer(self, endpoint, data, timeout, reading):
        policy = W.ULONG(timeout)
        if not self.api.WinUsb_SetPipePolicy(self.handle, endpoint, 3, C.sizeof(policy), C.byref(policy)):
            raise C.WinError(C.get_last_error())
        buffer = C.create_string_buffer(data) if isinstance(data, bytes) else C.create_string_buffer(data)
        length = len(data) if isinstance(data, bytes) else data
        transferred = W.ULONG()
        fn = self.api.WinUsb_ReadPipe if reading else self.api.WinUsb_WritePipe
        if not fn(self.handle, endpoint, buffer, length, C.byref(transferred), None):
            error = C.get_last_error()
            if reading and error in (121, 1460):
                raise usb.core.USBTimeoutError('WinUSB read timeout')
            raise C.WinError(error)
        return buffer.raw[:transferred.value] if reading else transferred.value

    def read(self, endpoint, size, timeout):
        return self.transfer(endpoint, size, timeout, True)

    def write(self, endpoint, data, timeout):
        return self.transfer(endpoint, data, timeout, False)

    def close(self):
        self.api.WinUsb_Free(self.handle)
        self.kernel.CloseHandle(self.file)
