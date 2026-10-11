// KYF37 supplemental HAL. Keep the OEM acceleration HAL; expose actual OEM interfaces.
#include <hardware/sensors.h>
#include <log/log.h>
#include <linux/input.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <array>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <fstream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace {
constexpr int N = 8;
// LUX is a standard android.sensor.light derived from the same 16-level LV5216 photosensor reading as PHOTO. Android's automatic
// brightness only listens to SENSOR_TYPE_LIGHT; PHOTO stays as the raw private level for calibration.
enum Kind { PHOTO, STEPS, WALK, VEHICLE, PICKUP, ORIENTATION, LID, LUX };
const char* names[N] = {"KYF37 ambient light level (0-15)", "KYF37 hardware step counter",
    "KYF37 walking state", "KYF37 vehicle state", "KYF37 pickup state",
    "KYF37 handset orientation", "KYF37 lid state", "KYF37 ambient light sensor"};
const char* strings[N] = {"org.kyf37.sensor.ambient_light_level", SENSOR_STRING_TYPE_STEP_COUNTER,
    "org.kyf37.sensor.walking", "org.kyf37.sensor.vehicle", "org.kyf37.sensor.pickup",
    "org.kyf37.sensor.handset_orientation", "org.kyf37.sensor.lid", SENSOR_STRING_TYPE_LIGHT};
// Approximate lux for each raw level 0..15 (log-like spacing; the chip's real transfer curve is not documented, calibrate later).
const float luxForLevel[16] = {0.f, 2.f, 6.f, 15.f, 35.f, 70.f, 120.f, 200.f, 320.f, 500.f, 800.f, 1200.f, 2000.f, 3500.f, 6000.f, 10000.f};
constexpr int typeOf(int i) { return i == 1 ? SENSOR_TYPE_STEP_COUNTER : (i == 7 ? SENSOR_TYPE_LIGHT : SENSOR_TYPE_DEVICE_PRIVATE_BASE + 1 + i); }
std::string paths[N], pedoEnable, motionEnable, vhEnable;
std::vector<sensor_t> sensors;
std::once_flag initialized;

std::string readText(const std::string& path) {
    std::ifstream input(path);
    std::string value;
    std::getline(input, value);
    return value;
}
int writeText(const std::string& path, const std::string& text) {
    int fd = open(path.c_str(), O_WRONLY | O_CLOEXEC);
    if (fd < 0) return -errno;
    ssize_t length;
    do { length = write(fd, text.data(), text.size()); } while (length < 0 && errno == EINTR);
    int result = length < 0 ? -errno : (size_t(length) == text.size() ? 0 : -EIO);
    close(fd);
    return result;
}
unsigned hexValue(const std::string& path) {
    unsigned value = 0;
    std::istringstream(readText(path)) >> std::hex >> value;
    return value;
}
void discover() {
    paths[PHOTO] = "/sys/class/leds/backlightinfo/ambient_light_level";
    for (int i = 0; i < 64; ++i) {
        std::string base = "/sys/class/input/input" + std::to_string(i) + "/";
        std::string name = readText(base + "name");
        if (name == "sensor_ext") {
            paths[STEPS] = base + "dailys_pedo_data";
            pedoEnable = base + "dailys_enable";
        } else if (name == "kc_motion_sensor") {
            paths[WALK] = base + "kc_motion_walk_data";
            paths[VEHICLE] = base + "kc_motion_vehi_data";
            paths[PICKUP] = base + "kc_motion_bringup_data";
            motionEnable = base + "kc_motion_enable";
        } else if (name == "vhdetect") {
            paths[ORIENTATION] = base + "vhdetect_data";
            vhEnable = base + "vhdetect_enable";
        }
    }
    for (int i = 0; i < 64; ++i) {
        std::string base = "/sys/class/input/event" + std::to_string(i);
        if (readText(base + "/device/name") == "gpio-keys")
            paths[LID] = "/dev/input/event" + std::to_string(i);
    }
    paths[LUX] = paths[PHOTO];
    for (int i = 0; i < N; ++i) {
        if (paths[i].empty() || access(paths[i].c_str(), F_OK) != 0) continue;
        sensor_t sensor = {};
        sensor.name = names[i]; sensor.vendor = "Kyocera"; sensor.version = 1;
        sensor.handle = 100 + i;
        sensor.type = typeOf(i);
        sensor.maxRange = i == STEPS ? 4294967295.0f : (i == PHOTO ? 15.0f : (i == LUX ? 10000.0f : 255.0f));
        sensor.resolution = 1; sensor.power = 0.2f;
        sensor.stringType = strings[i]; sensor.requiredPermission = "";
        sensor.maxDelay = 1000000;
        sensor.flags = SENSOR_FLAG_ON_CHANGE_MODE;
        sensors.push_back(sensor);
    }
}
int list(sensors_module_t*, const sensor_t** out) {
    std::call_once(initialized, discover);
    *out = sensors.data(); return sensors.size();
}
int64_t now() {
    timespec ts; clock_gettime(CLOCK_BOOTTIME, &ts);
    return int64_t(ts.tv_sec) * 1000000000 + ts.tv_nsec;
}
struct Context {
    sensors_poll_device_1_t device{};
    std::mutex mutex;
    std::condition_variable condition;
    bool stopping = false;
    std::array<bool,N> active{}, valid{};
    std::array<std::string,N> last{};
    std::deque<sensors_event_t> queue;
    std::thread worker;
    unsigned priorPedo = 0, priorMotion = 0, priorVh = 0;
    uint64_t steps = 0;
    uint32_t previousRaw = 0;
    bool haveSteps = false;

    int controls() {
        if (!pedoEnable.empty()) {
            int r = writeText(pedoEnable, std::string("1 ") + ((active[STEPS] || (priorPedo & 1)) ? "1 fa\n" : "0 fa\n"));
            if (r) return r;
        }
        if (!motionEnable.empty()) {
            const unsigned bits[] = {1, 2, 4, 8, 16};
            for (unsigned bit : bits) {
                bool enabled = (priorMotion & bit) || (bit <= 2 && active[WALK]) ||
                    (bit == 8 && active[VEHICLE]) || (bit == 16 && active[PICKUP]);
                std::ostringstream value;
                value << std::hex << bit << (enabled ? " 1\n" : " 0\n");
                int r = writeText(motionEnable, value.str());
                if (r) return r;
            }
        }
        if (!vhEnable.empty()) return writeText(vhEnable, (active[ORIENTATION] || priorVh) ? "1\n" : "0\n");
        return 0;
    }
    void sample(int i) {
        std::string text;
        if (i == LID) {
            int fd = open(paths[i].c_str(), O_RDONLY | O_CLOEXEC);
            if (fd < 0) return;
            unsigned long switches = 0;
            int result = ioctl(fd, EVIOCGSW(sizeof(switches)), &switches);
            close(fd);
            if (result < 0) return;
            text = (switches & (1UL << SW_LID)) ? "1" : "0";
        } else text = readText(paths[i]);
        if (text.empty()) return;
        sensors_event_t event = {};
        event.version = sizeof(event); event.sensor = 100 + i;
        event.type = typeOf(i);
        event.timestamp = now();
        std::istringstream input(text);
        if (i == STEPS) {
            uint64_t raw;
            if (!(input >> raw) || raw > UINT32_MAX) return;
            uint32_t current = raw;
            if (!haveSteps) { steps = current; haveSteps = true; }
            else if (current >= previousRaw) steps += current - previousRaw;
            else if (previousRaw > 0xf0000000 && current < 0x10000000)
                steps += uint32_t(current - previousRaw);
            else steps += current; // hub reset: preserve Android's monotonic counter.
            previousRaw = current;
            text = std::to_string(steps);
            event.u64.step_counter = steps;
        } else {
            if (!(input >> event.data[0])) return;
            if ((i == PHOTO || i == LUX) && (event.data[0] < 0 || event.data[0] > 15)) return;
            if (i == LUX) {
                int level = int(event.data[0]);
                event.data[0] = luxForLevel[level];
                text = std::to_string(level);   // report only when the raw level changes
            }
            if (i == VEHICLE && !(input >> event.data[1])) return;
        }
        if (valid[i] && last[i] == text) return;
        valid[i] = true; last[i] = text;
        if (queue.size() < 256) queue.push_back(event);
    }
    void run() {
        std::unique_lock<std::mutex> guard(mutex);
        while (!stopping) {
            bool enabled = false;
            for (int i = 0; i < N; ++i) if (active[i]) { enabled = true; sample(i); }
            if (!queue.empty()) condition.notify_all();
            if (enabled) condition.wait_for(guard, std::chrono::milliseconds(250));
            else condition.wait(guard);
        }
    }
};
bool known(int handle) {
    for (const sensor_t& sensor : sensors) if (sensor.handle == handle) return true;
    return false;
}
int activate(sensors_poll_device_t* device, int handle, int enable) {
    if (!known(handle)) return -EINVAL;
    Context* ctx = reinterpret_cast<Context*>(device);
    std::lock_guard<std::mutex> guard(ctx->mutex);
    int index = handle - 100;
    bool old = ctx->active[index]; ctx->active[index] = enable != 0;
    int result = ctx->controls();
    if (result) { ctx->active[index] = old; ctx->controls(); return result; }
    ctx->valid[index] = false;
    ctx->condition.notify_all(); return 0;
}
int delay(sensors_poll_device_t*, int handle, int64_t) { return known(handle) ? 0 : -EINVAL; }
int batch(sensors_poll_device_1_t*, int handle, int flags, int64_t period, int64_t latency) {
    if (!known(handle) || flags || period < 0 || latency < 0) return -EINVAL;
    return 0; // On-change reporting, no FIFO/batching advertised.
}
int flush(sensors_poll_device_1_t* device, int handle) {
    if (!known(handle)) return -EINVAL;
    Context* ctx = reinterpret_cast<Context*>(device);
    std::lock_guard<std::mutex> guard(ctx->mutex);
    if (!ctx->active[handle - 100]) return -EINVAL;
    ctx->sample(handle - 100);
    sensors_event_t event = {}; event.version = sizeof(event);
    event.type = SENSOR_TYPE_META_DATA;
    event.meta_data.what = META_DATA_FLUSH_COMPLETE; event.meta_data.sensor = handle;
    ctx->queue.push_back(event); ctx->condition.notify_all(); return 0;
}
int pollEvents(sensors_poll_device_t* device, sensors_event_t* events, int count) {
    if (!events || count <= 0) return -EINVAL;
    Context* ctx = reinterpret_cast<Context*>(device);
    std::unique_lock<std::mutex> guard(ctx->mutex);
    ctx->condition.wait(guard, [ctx]{ return ctx->stopping || !ctx->queue.empty(); });
    if (ctx->stopping) return -ENODEV;
    int n = 0;
    while (n < count && !ctx->queue.empty()) { events[n++] = ctx->queue.front(); ctx->queue.pop_front(); }
    return n;
}
int closeDevice(hw_device_t* device) {
    Context* ctx = reinterpret_cast<Context*>(device);
    { std::lock_guard<std::mutex> guard(ctx->mutex); ctx->stopping = true; ctx->condition.notify_all(); }
    ctx->worker.join();
    ctx->active.fill(false); ctx->controls(); delete ctx; return 0;
}
int openDevice(const hw_module_t* module, const char* name, hw_device_t** output) {
    if (!output || !name || std::string(name) != SENSORS_HARDWARE_POLL) return -EINVAL;
    std::call_once(initialized, discover);
    Context* ctx = new Context;
    ctx->priorPedo = hexValue(pedoEnable); ctx->priorMotion = hexValue(motionEnable); ctx->priorVh = hexValue(vhEnable);
    ctx->device.common.tag = HARDWARE_DEVICE_TAG;
    ctx->device.common.version = SENSORS_DEVICE_API_VERSION_1_3;
    ctx->device.common.module = const_cast<hw_module_t*>(module);
    ctx->device.common.close = closeDevice;
    ctx->device.activate = activate; ctx->device.setDelay = delay; ctx->device.poll = pollEvents;
    ctx->device.batch = batch; ctx->device.flush = flush;
    ctx->worker = std::thread([ctx]{ ctx->run(); });
    *output = &ctx->device.common; return 0;
}
hw_module_methods_t methods = {.open = openDevice};
} // namespace

extern "C" sensors_module_t HAL_MODULE_INFO_SYM = {
    .common = {.tag = HARDWARE_MODULE_TAG, .module_api_version = SENSORS_MODULE_API_VERSION_0_1,
        .hal_api_version = HARDWARE_HAL_API_VERSION, .id = SENSORS_HARDWARE_MODULE_ID,
        .name = "KYF37 additional hardware sensors", .author = "althia", .methods = &methods},
    .get_sensors_list = list,
};
