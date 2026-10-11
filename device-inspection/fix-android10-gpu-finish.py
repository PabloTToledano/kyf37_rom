from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp')
s=p.read_text()
a='''base::unique_fd GLESRenderEngine::flush() {
    ATRACE_CALL();
'''
b='''base::unique_fd GLESRenderEngine::flush() {
    ATRACE_CALL();
    // KYF37: the Adreno 304 userspace fence is not reliable and the MDP3 video-mode
    // panel scans the client target directly. Finish the frame before it is handed over.
    glFinish();
'''
if 'KYF37: the Adreno 304 userspace fence' not in s:
    assert s.count(a)==1
    p.write_text(s.replace(a,b))
print('ok')
