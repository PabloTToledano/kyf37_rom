#!/system/bin/sh
# Preserve Qualcomm hardware initialization, then apply the balanced policy.
/system/bin/sh /system/etc/init.qcom.post_boot.sh "$@"
vendor_status=$?
/system/bin/sh /kyf37-performance-policy.sh
exit "$vendor_status"
