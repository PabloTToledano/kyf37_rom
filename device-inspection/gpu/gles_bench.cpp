// KYF37 GPU sanity/benchmark: offscreen (pbuffer) GLES2 rendering through the real Adreno driver.
// Prints renderer strings and ms/frame for (a) trivial fill, (b) textured blend (2D-like blit), (c) ALU-heavy shader.
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_ms() { timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000.0 + t.tv_nsec / 1e6; }

static GLuint sh(GLenum type, const char* src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    GLint ok = 0; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char log[1024]; glGetShaderInfoLog(s, sizeof log, nullptr, log); printf("shader error: %s\n", log); exit(2); }
    return s;
}
static GLuint prog(const char* fs) {
    const char* vs = "attribute vec2 p; varying vec2 uv; void main(){ uv=p*0.5+0.5; gl_Position=vec4(p,0.0,1.0);} ";
    GLuint pr = glCreateProgram();
    glAttachShader(pr, sh(GL_VERTEX_SHADER, vs));
    glAttachShader(pr, sh(GL_FRAGMENT_SHADER, fs));
    glBindAttribLocation(pr, 0, "p");
    glLinkProgram(pr);
    GLint ok = 0; glGetProgramiv(pr, GL_LINK_STATUS, &ok);
    if (!ok) { printf("link error\n"); exit(3); }
    return pr;
}
static void run(const char* name, GLuint pr, int frames, bool blend) {
    static const GLfloat quad[] = {-1,-1, 1,-1, -1,1, 1,1};
    glUseProgram(pr);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, quad);
    glEnableVertexAttribArray(0);
    if (blend) { glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA); } else glDisable(GL_BLEND);
    for (int i = 0; i < 3; i++) { glDrawArrays(GL_TRIANGLE_STRIP, 0, 4); }
    glFinish();
    double t0 = now_ms();
    for (int i = 0; i < frames; i++) { glDrawArrays(GL_TRIANGLE_STRIP, 0, 4); if ((i & 7) == 7) glFinish(); }
    glFinish();
    double ms = (now_ms() - t0) / frames;
    printf("%-28s %8.3f ms/frame  %7.1f fps  %6.1f Mpix/s\n", name, ms, 1000.0 / ms, 480.0 * 854.0 / 1e6 / (ms / 1000.0));
}
int main() {
    EGLDisplay d = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint maj, min;
    if (!eglInitialize(d, &maj, &min)) { printf("eglInitialize failed %x\n", eglGetError()); return 1; }
    printf("EGL %d.%d vendor=%s\n", maj, min, eglQueryString(d, EGL_VENDOR));
    const EGLint ca[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE};
    EGLConfig cfg; EGLint n = 0;
    if (!eglChooseConfig(d, ca, &cfg, 1, &n) || n < 1) { printf("no config %x\n", eglGetError()); return 1; }
    const EGLint pa[] = {EGL_WIDTH, 480, EGL_HEIGHT, 854, EGL_NONE};
    EGLSurface s = eglCreatePbufferSurface(d, cfg, pa);
    const EGLint xa[] = {EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE};
    EGLContext c = eglCreateContext(d, cfg, EGL_NO_CONTEXT, xa);
    if (s == EGL_NO_SURFACE || c == EGL_NO_CONTEXT || !eglMakeCurrent(d, s, s, c)) { printf("context failed %x\n", eglGetError()); return 1; }
    printf("GL_VENDOR   %s\nGL_RENDERER %s\nGL_VERSION  %s\n", glGetString(GL_VENDOR), glGetString(GL_RENDERER), glGetString(GL_VERSION));
    glViewport(0, 0, 480, 854);
    GLuint tex; glGenTextures(1, &tex); glBindTexture(GL_TEXTURE_2D, tex);
    static unsigned char img[256 * 256 * 4]; for (int i = 0; i < 256 * 256 * 4; i++) img[i] = (unsigned char)(i * 7);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_RGBA, GL_UNSIGNED_BYTE, img);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    GLuint a = prog("precision mediump float; varying vec2 uv; void main(){ gl_FragColor=vec4(uv,0.5,1.0);} ");
    GLuint b = prog("precision mediump float; varying vec2 uv; uniform sampler2D t; void main(){ gl_FragColor=texture2D(t,uv)*vec4(1.0,1.0,1.0,0.5);} ");
    GLuint e = prog("precision mediump float; varying vec2 uv; void main(){ float x=uv.x*9.0, y=uv.y*9.0; for(int i=0;i<24;i++){ x=sin(y+x*0.7)+cos(x*1.3); y=cos(x+y*0.9)-sin(y*1.1);} gl_FragColor=vec4(0.5+0.5*x,0.5+0.5*y,0.5,1.0);} ");
    glUseProgram(b); glUniform1i(glGetUniformLocation(b, "t"), 0);
    run("fill (flat shader)", a, 300, false);
    run("2D-like textured blend", b, 300, true);
    run("3D ALU-heavy (24x sin/cos)", e, 60, false);
    // texture upload bandwidth (2D bitmap upload path)
    double t0 = now_ms();
    for (int i = 0; i < 50; i++) glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE, img);
    glFinish();
    double ms = (now_ms() - t0) / 50;
    printf("%-28s %8.3f ms/upload %6.1f MB/s\n", "256x256 RGBA tex upload", ms, 256.0 * 256 * 4 / 1e6 / (ms / 1000.0));
    printf("GL_ERROR 0x%x\n", glGetError());
    return 0;
}
