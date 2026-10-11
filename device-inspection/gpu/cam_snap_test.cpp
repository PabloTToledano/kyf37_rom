// KYF37 camera HAL1 capture test (no app involved): connect, preview, takePicture, save the JPEG to argv[1].
// Prints every callback so a failing snapshot path is visible.
#include <camera/Camera.h>
#include <camera/CameraParameters.h>
#include <gui/BufferItemConsumer.h>
#include <gui/BufferQueue.h>
#include <binder/ProcessState.h>
#include <binder/IMemory.h>
#include <utils/String8.h>
#include <utils/Mutex.h>
#include <utils/Condition.h>
#include <stdio.h>
#include <unistd.h>
#include <string>
using namespace android;

static Mutex gLock; static Condition gCond; static bool gDone = false; static std::string gOut = "/data/local/tmp/snap.jpg";

struct Listener : public CameraListener {
    void notify(int32_t msgType, int32_t ext1, int32_t ext2) override { printf("notify msg=0x%x ext1=%d ext2=%d\n", msgType, ext1, ext2); fflush(stdout); }
    void postData(int32_t msgType, const sp<IMemory>& data, camera_frame_metadata_t*) override {
        ssize_t off; size_t size; sp<IMemory> d = data;
        if (d == nullptr) { printf("postData msg=0x%x (null)\n", msgType); fflush(stdout); return; }
        sp<IMemoryHeap> heap = d->getMemory(&off, &size);
        printf("postData msg=0x%x size=%zu\n", msgType, size); fflush(stdout);
        if (msgType & CAMERA_MSG_COMPRESSED_IMAGE) {
            FILE* f = fopen(gOut.c_str(), "wb");
            if (f) { fwrite((const char*)heap->base() + off, 1, size, f); fclose(f); printf("saved %s (%zu bytes)\n", gOut.c_str(), size); }
            Mutex::Autolock l(gLock); gDone = true; gCond.signal();
        }
    }
    void postDataTimestamp(nsecs_t, int32_t msgType, const sp<IMemory>&) override { printf("postDataTimestamp 0x%x\n", msgType); }
    void postRecordingFrameHandleTimestamp(nsecs_t, native_handle_t*) override {}
    void postRecordingFrameHandleTimestampBatch(const std::vector<nsecs_t>&, const std::vector<native_handle_t*>&) override {}
};
struct Drain : public BufferItemConsumer::FrameAvailableListener {
    wp<BufferItemConsumer> c; int n = 0;
    void onFrameAvailable(const BufferItem&) override {
        sp<BufferItemConsumer> s = c.promote(); if (!s) return; BufferItem item;
        if (s->acquireBuffer(&item, 0) == OK) { s->releaseBuffer(item); n++; }
    }
    void onFrameReplaced(const BufferItem&) override {}
};
int main(int argc, char** argv) {
    if (argc > 1) gOut = argv[1];
    ProcessState::self()->startThreadPool();
    sp<Camera> cam = Camera::connect(0, String16("kyf37.camtest"), Camera::USE_CALLING_UID, Camera::USE_CALLING_PID);
    if (cam == nullptr) { printf("connect failed\n"); return 1; }
    printf("connected\n"); fflush(stdout);
    cam->setListener(new Listener());
    sp<IGraphicBufferProducer> prod; sp<IGraphicBufferConsumer> cons; BufferQueue::createBufferQueue(&prod, &cons);
    sp<BufferItemConsumer> bic = new BufferItemConsumer(cons, GRALLOC_USAGE_HW_TEXTURE, 4);
    sp<Drain> drain = new Drain(); drain->c = bic; bic->setFrameAvailableListener(drain);
    CameraParameters p(cam->getParameters());
    printf("params: %s\n", p.flatten().string()); fflush(stdout);
    if (cam->setPreviewTarget(prod) != OK) { printf("setPreviewTarget failed\n"); return 2; }
    if (cam->startPreview() != OK) { printf("startPreview failed\n"); return 3; }
    printf("preview started\n"); fflush(stdout);
    sleep(3);
    printf("preview frames drained: %d\n", drain->n);
    status_t r = cam->takePicture(CAMERA_MSG_SHUTTER | CAMERA_MSG_COMPRESSED_IMAGE);
    printf("takePicture -> %d\n", r); fflush(stdout);
    Mutex::Autolock l(gLock);
    if (!gDone) gCond.waitRelative(gLock, 15000000000LL);
    printf(gDone ? "RESULT: got JPEG\n" : "RESULT: timed out waiting for JPEG\n");
    cam->stopPreview(); cam->disconnect();
    return gDone ? 0 : 4;
}
