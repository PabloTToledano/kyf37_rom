// KYF37: symbols the stock Qualcomm JPEG stack (libfastcvopt / libmmqjpeg_codec) needs that Android 10 no longer exports.
// Preloaded into the camera provider (LD_PRELOAD) so the linker can resolve them.
extern "C" {
// Old ARM EABI runtime hook called on division by zero; the stock libgcc/bionic provided it. Returning makes the quotient 0.
void __aeabi_idiv0(void) {}
void __aeabi_ldiv0(void) {}
// BoringSSL has no EVP_Seal*; the codec only uses them for optional encrypted output, which we never request.
int EVP_SealInit(void*, const void*, unsigned char**, int*, unsigned char*, void**, int) { return 0; }
int EVP_SealUpdate(void*, unsigned char*, int*, const unsigned char*, int) { return 0; }
int EVP_SealFinal(void*, unsigned char*, int*) { return 0; }
int EVP_OpenInit(void*, const void*, const unsigned char*, int, const unsigned char*, void*) { return 0; }
int EVP_OpenUpdate(void*, unsigned char*, int*, const unsigned char*, int) { return 0; }
int EVP_OpenFinal(void*, unsigned char*, int*) { return 0; }
// libmmjpeg walks the stack itself (allocation tracing). Its frames use the old EHABI compact personality routines
// (__aeabi_unwind_cpp_pr0/1), which bionic implements as an illegal-instruction trap, so the walk raised SIGILL in
// mm_jpeg_thread. The trace is only diagnostic: report an empty stack.
int _Unwind_Backtrace(int (*)(void*, void*), void*) { return 0; }
// Qualcomm perf-lock client API. libmmcamera_imglib/libmmqjpeg_codec dlopen() the library named by
// ro.vendor.extension_library and dlsym() these; if it is missing img_perf_handle_create returns NULL and the stock
// img_perf_handle_destroy then dereferences NULL (SIGSEGV in OMX_ImgEnc right after a successful JPEG encode).
// We have no perf daemon client on this ROM: no-op implementations are enough (ro.vendor.extension_library points here).
int perf_lock_acq(int, int, int*, int) { return 1; }
int perf_lock_rel(int) { return 0; }
// The stock JPEG codec destroys mutexes that are already destroyed or still referenced (QImageHybridEncoder::ReleaseSession).
// Old bionic ignored that; Android 10's pthread_mutex_destroy aborts the whole provider (__fortify_fatal). This shim is only
// preloaded into the camera provider, where leaking a few bytes of mutex state is harmless.
int pthread_mutex_destroy(void*) { return 0; }
}
