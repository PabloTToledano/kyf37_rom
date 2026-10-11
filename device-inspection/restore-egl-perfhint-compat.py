"""Apply between builds; restore model HWC's EGL extension entry point."""
from pathlib import Path
p=Path('/home/pablo/kyf37-lineage/frameworks/native/opengl/libs/EGL/eglApi.cpp')
s=p.read_text()
function='''
// Model HWC ABI: unwrap Android handles before invoking the driver extension.
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
'''
s=s.replace('    egl_connection_t * const connection = c->cnx;',
            '    const egl_connection_t * const connection = c->cnx;')
p.write_text(s)
if 'EGLBoolean eglGpuPerfHintQCOM(' not in s:
    assert 'EGLBoolean eglQueryContext(' in s
    p.write_text(s+function)
print('EGL performance hint forwarding restored with handle translation.')
