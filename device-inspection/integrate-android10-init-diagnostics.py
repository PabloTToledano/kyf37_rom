"""Marker-gated cache logging and recovery guard for development boot tests."""
from pathlib import Path
import subprocess

assert subprocess.run(['pgrep', '-x', 'ninja'], stdout=subprocess.DEVNULL).returncode != 0
p = Path('/home/pablo/kyf37-android10/system/core/init/util.cpp')
s = p.read_text()
marker = '// KYF37 opt-in boot diagnostics; no formatting or image writes.'
if marker in s:
    raise SystemExit('Diagnostics already integrated')
s = s.replace('#include <sys/socket.h>', '#include <sys/mount.h>\n#include <sys/stat.h>\n#include <sys/sysmacros.h>\n#include <sys/socket.h>', 1)
code = r'''
// KYF37 opt-in boot diagnostics; no formatting or image writes.
static bool Kyf37DebugEnabled() {
    return getpid() == 1 && access("/kyf37-init-debug", F_OK) == 0;
}

static bool Kyf37Geometry(const char* part, const char* start, const char* size) {
    std::string value;
    const std::string path = std::string("/sys/class/block/") + part;
    return android::base::ReadFileToString(path + "/start", &value) &&
           android::base::Trim(value) == start &&
           android::base::ReadFileToString(path + "/size", &value) &&
           android::base::Trim(value) == size;
}

static void Kyf37RecoveryGuard() {
    if (!Kyf37DebugEnabled() || !Kyf37Geometry("mmcblk0p21", "15022080", "2048")) return;
    mknod("/dev/kyf37-debug-misc", S_IFBLK | 0600, makedev(179, 21));
    android::base::unique_fd fd(open("/dev/kyf37-debug-misc", O_RDWR | O_CLOEXEC));
    char before[33] = {}, command[32] = {};
    if (fd < 0 || pread(fd, before, 32, 0) != 32) return;
    if (before[0] != 0 && strcmp(before, "boot-recovery") != 0) return;
    memcpy(command, "boot-recovery", 13);
    if (pwrite(fd, command, sizeof(command), 0) == sizeof(command)) fsync(fd);
}

static void Kyf37DebugSetup() {
    if (!Kyf37DebugEnabled()) return;
    Kyf37RecoveryGuard();
    if (!Kyf37Geometry("mmcblk0p17", "3457024", "2049024")) return;
    mkdir("/kyf37-debug", 0700);
    mknod("/dev/kyf37-debug-cache", S_IFBLK | 0600, makedev(179, 17));
    mount("/dev/kyf37-debug-cache", "/kyf37-debug", "ext4", MS_NOSUID | MS_NODEV, nullptr);
    // Every stage reopens the same file; keep descriptors out of exec boundaries.
    android::base::unique_fd fd(open("/kyf37-debug/kyf37-init.log", O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600));
    if (fd >= 0) { dprintf(fd, "\nKYF37 diagnostic init stage pid=%d\n", getpid()); fsync(fd); }
}

static void Kyf37DebugLogger(android::base::LogId id, android::base::LogSeverity severity,
                            const char* tag, const char* file, unsigned int line,
                            const char* message) {
    android::base::KernelLogger(id, severity, tag, file, line, message);
    if (!Kyf37DebugEnabled()) return;
    android::base::unique_fd fd(open("/kyf37-debug/kyf37-init.log", O_WRONLY | O_APPEND | O_CLOEXEC));
    if (fd >= 0) {
        dprintf(fd, "pid=%d severity=%d %s:%u %s\n", getpid(), static_cast<int>(severity), file ? file : "", line, message);
        fsync(fd);
    }
}

'''
s = s.replace('static void InitAborter(const char* abort_message) {', code + 'static void InitAborter(const char* abort_message) {', 1)
s = s.replace('    InitFatalReboot();\n}', '    Kyf37RecoveryGuard();\n    InitFatalReboot();\n}', 1)
old = 'void InitKernelLogging(char** argv) {\n    SetFatalRebootTarget();\n    android::base::InitLogging(argv, &android::base::KernelLogger, InitAborter);\n}'
new = 'void InitKernelLogging(char** argv) {\n    SetFatalRebootTarget();\n    Kyf37DebugSetup();\n    android::base::InitLogging(argv, &Kyf37DebugLogger, InitAborter);\n}'
assert old in s
p.write_text(s.replace(old, new, 1))
print('Integrated marker-gated diagnostics; keep marker absent in normal release images.')
