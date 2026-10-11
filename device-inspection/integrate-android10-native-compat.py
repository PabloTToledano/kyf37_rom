"""Apply with no build running: preserve semantics of three legacy vendor APIs."""
from pathlib import Path
import subprocess
tree = Path('/home/pablo/kyf37-android10')
assert subprocess.run(['pgrep', '-x', 'ninja'], stdout=subprocess.DEVNULL).returncode != 0, 'Stop the build first'
threads = tree/'system/core/libutils/Threads.cpp'
s = threads.read_text()
if 'pid_t androidGetTid()' not in s:
    if '#include <unistd.h>' not in s:
        s = s.replace('#if defined(__linux__)\n', '#if defined(__linux__)\n#include <unistd.h>\n', 1)
    threads.write_text(s+'''\n// Qualcomm legacy media ABI: return the Linux thread ID.
#if defined(__ANDROID__)
extern "C" pid_t androidGetTid() { return gettid(); }
#endif
''')

# Android 10 declares this compatibility API in rsa.h but normally only
# provides it in libdecrepit. Move its exact implementation into libcrypto,
# the provider the stock Adreno binary actually links against.
padding = tree/'external/boringssl/src/crypto/fipsmodule/rsa/padding.c'
decrepit = tree/'external/boringssl/src/decrepit/rsa/rsa_decrepit.c'
function = '''int RSA_verify_PKCS1_PSS(const RSA *rsa, const uint8_t *mHash,
                         const EVP_MD *Hash, const uint8_t *EM, int sLen) {
  return RSA_verify_PKCS1_PSS_mgf1(rsa, mHash, Hash, NULL, EM, sLen);
}
'''
s = padding.read_text()
if 'int RSA_verify_PKCS1_PSS(' not in s:
    assert function in decrepit.read_text()
    padding.write_text(s+'\n/* Legacy Adreno ABI: same PSS verification, shared provider. */\n'+function)
    decrepit.write_text(decrepit.read_text().replace(function, ''))

egl = tree/'frameworks/native/opengl/libs/EGL/eglApi.cpp'
s = egl.read_text()
if 'EGLBoolean eglGpuPerfHintQCOM(' not in s:
    s = s.replace('#include "egl_layers.h"', '#include "egl_display.h"\n#include "egl_object.h"\n#include "egl_layers.h"')
    egl.write_text(s+'''
// Qualcomm HWC ABI: translate platform handles before calling the driver.
extern "C" __attribute__((visibility("default")))
EGLBoolean eglGpuPerfHintQCOM(EGLDisplay display, EGLContext context,
                              EGLint *attributes) {
    clearError();
    const egl_display_ptr dp = validate_display(display);
    if (!dp) return EGL_FALSE;
    ContextRef reference(dp.get(), context);
    if (!reference.get()) return setError(EGL_BAD_CONTEXT, EGL_FALSE);
    egl_context_t * const c = get_context(context);
    const egl_connection_t * const connection = c->cnx;
    if (!connection->dso || !connection->egl.eglGetProcAddress)
        return EGL_FALSE;
    typedef EGLBoolean (*HintFunction)(EGLDisplay, EGLContext, EGLint *);
    HintFunction hint = reinterpret_cast<HintFunction>(
        connection->egl.eglGetProcAddress("eglGpuPerfHintQCOM"));
    if (!hint) return EGL_FALSE;
    return hint(dp->disp.dpy, c->context, attributes);
}
''')
print('Thread ID, shared PSS verifier and HWC EGL hint compatibility integrated; compilation/runtime checks pending.')
