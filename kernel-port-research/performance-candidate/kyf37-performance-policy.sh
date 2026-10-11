#!/system/bin/sh
# One-shot balanced policy. No polling, frequency cap, voltage or thermal edits.
# SYSFS_ROOT exists only to run this same script against host-test fixtures.
sysfs_root=${KYF37_SYSFS_ROOT:-/sys}

write_if_present() {
    [ -w "$1" ] || return 0
    printf '%s\n' "$2" > "$1"
}

positive_integer() {
    case "$1" in ''|*[!0-9]*) return 1 ;; esac
    [ "$1" -gt 0 ] 2>/dev/null
}

policy="$sysfs_root/devices/system/cpu/cpu0/cpufreq"
available=$(cat "$policy/scaling_available_governors" 2>/dev/null)
case " $available " in
    *' interactive '*) write_if_present "$policy/scaling_governor" interactive ;;
esac
minimum=$(cat "$policy/cpuinfo_min_freq" 2>/dev/null)
maximum=$(cat "$policy/scaling_max_freq" 2>/dev/null)
if positive_integer "$minimum" && positive_integer "$maximum" &&
        [ "$minimum" -le "$maximum" ]; then
    write_if_present "$policy/scaling_min_freq" "$minimum"
fi

# Qualcomm's MSM8909 target_loads begins with 1, forcing a rapid jump out of
# low frequencies even after the 800 MHz minimum is removed. Allow proportional
# scaling instead. Retain its hispeed/timer/min-sample settings for responsiveness.
governor=$(cat "$policy/scaling_governor" 2>/dev/null)
if [ "$governor" = interactive ]; then
    write_if_present "$sysfs_root/devices/system/cpu/cpufreq/interactive/target_loads" 85
fi

# Keep the vendor's automatic hotplug and thermal protection; permit one core
# at light load instead of holding two online. Existing thresholds remain intact.
write_if_present "$sysfs_root/devices/system/cpu/cpu0/core_ctl/min_cpus" 1

# Bound speculative eMMC reads on this 1 GB device. Do not increase a smaller
# existing setting, or alter removable-storage queues or the I/O scheduler.
read_ahead="$sysfs_root/block/mmcblk0/queue/read_ahead_kb"
current=$(cat "$read_ahead" 2>/dev/null)
if positive_integer "$current" && [ "$current" -gt 128 ]; then
    write_if_present "$read_ahead" 128
fi

# CFQ idles waiting for more requests from a process. That helps rotating disks;
# on eMMC it only adds latency and keeps the storage busy. These tunables exist
# only while CFQ is the active scheduler, so nothing is touched otherwise.
iosched="$sysfs_root/block/mmcblk0/queue/iosched"
write_if_present "$iosched/slice_idle" 0
write_if_present "$iosched/group_idle" 0
exit 0
